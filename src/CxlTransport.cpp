#include "CxlTransport.h"
#include "Debug.h"

#include <sys/mman.h>
#include <numaif.h>
#include <numa.h>
#include <cerrno>
#include <cstdio>

// ---- Constructor / Destructor ----

CxlTransport::CxlTransport(int numa_node, size_t pool_size, size_t lock_size,
                             int machine_nr, bool use_hugepages)
    : base_addr_(nullptr),
      lock_addr_(nullptr),
      pool_size_(pool_size),
      lock_size_(lock_size),
      numa_node_(numa_node),
      machine_nr_(machine_nr),
      my_node_id_(0),
      alloc_offset_(0),
      barrier_initialized_(false) {

  // Allocate main memory pool
  int flags = MAP_PRIVATE | MAP_ANONYMOUS;
  if (use_hugepages) {
    flags |= MAP_HUGETLB;
  }

  base_addr_ = mmap(nullptr, pool_size_, PROT_READ | PROT_WRITE, flags, -1, 0);
  if (base_addr_ == MAP_FAILED) {
    Debug::notifyError("CxlTransport: failed to mmap %zu bytes for pool (errno=%d: %s)",
                       pool_size_, errno, strerror(errno));
    base_addr_ = nullptr;
    return;
  }

  // Bind to remote NUMA node (emulates CXL-attached memory)
  if (numa_available() >= 0) {
    unsigned long nodemask = 1UL << numa_node;
    long ret = mbind(base_addr_, pool_size_, MPOL_BIND, &nodemask,
                     sizeof(nodemask) * 8, MPOL_MF_MOVE | MPOL_MF_STRICT);
    if (ret != 0) {
      Debug::notifyInfo("CxlTransport: mbind to NUMA node %d failed (errno=%d), "
                        "continuing with default policy", numa_node, errno);
    }
  }

  // Zero-fill to fault in pages
  memset(base_addr_, 0, pool_size_);

  // Allocate lock region (smaller, emulates on-chip NIC memory)
  lock_addr_ = mmap(nullptr, lock_size_, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
  if (lock_addr_ == MAP_FAILED) {
    Debug::notifyError("CxlTransport: failed to mmap %zu bytes for lock region", lock_size_);
    lock_addr_ = nullptr;
    return;
  }
  memset(lock_addr_, 0, lock_size_);

  // Initialize barrier for multi-thread coordination
  if (machine_nr > 0) {
    pthread_barrier_init(&barrier_, nullptr, machine_nr);
    barrier_initialized_ = true;
  }

  Debug::notifyInfo("CxlTransport initialized: pool=%zuMB lock=%zuKB numa=%d",
                    pool_size_ / (1024 * 1024), lock_size_ / 1024, numa_node_);
}

CxlTransport::~CxlTransport() {
  if (base_addr_ && base_addr_ != MAP_FAILED) {
    munmap(base_addr_, pool_size_);
  }
  if (lock_addr_ && lock_addr_ != MAP_FAILED) {
    munmap(lock_addr_, lock_size_);
  }
  if (barrier_initialized_) {
    pthread_barrier_destroy(&barrier_);
  }
}

// ---- One-sided read/write ----

void CxlTransport::read_sync(char *buffer, GlobalAddress gaddr, size_t size) {
  memcpy(buffer, resolve(gaddr), size);
}

void CxlTransport::write_sync(const char *buffer, GlobalAddress gaddr, size_t size) {
  memcpy(resolve(gaddr), buffer, size);
}

// ---- Batch operations ----

void CxlTransport::read_batch_sync(CxlOpRegion *rs, int count) {
  for (int i = 0; i < count; i++) {
    memcpy(reinterpret_cast<char *>(rs[i].source), resolve(rs[i].dest), rs[i].size);
  }
}

void CxlTransport::write_batch_sync(CxlOpRegion *rs, int count) {
  for (int i = 0; i < count; i++) {
    memcpy(resolve(rs[i].dest), reinterpret_cast<const char *>(rs[i].source), rs[i].size);
  }
}

// ---- Atomic operations (internal helpers) ----

bool CxlTransport::cas_internal(void *target, uint64_t equal, uint64_t val,
                                 uint64_t *result) {
  auto *ptr = static_cast<uint64_t *>(target);
  *result = __sync_val_compare_and_swap(ptr, equal, val);
  return (*result == equal);
}

bool CxlTransport::cas_mask_internal(void *target, uint64_t equal, uint64_t val,
                                      uint64_t *result,
                                      uint64_t compare_mask, uint64_t swap_mask) {
  auto *ptr = static_cast<uint64_t *>(target);

  // Read-modify-CAS loop to emulate masked CAS
  // This is the simplest correct implementation (Option A from spec)
  for (int retry = 0; retry < 1000000; retry++) {
    uint64_t current = __atomic_load_n(ptr, __ATOMIC_SEQ_CST);

    // Check if masked bits match
    if ((current & compare_mask) != (equal & compare_mask)) {
      *result = current;
      return false;
    }

    // Compute new value: keep non-masked bits, swap masked bits
    uint64_t new_val = (current & ~swap_mask) | (val & swap_mask);

    if (__sync_bool_compare_and_swap(ptr, current, new_val)) {
      *result = current;
      return true;
    }
    // CAS failed due to concurrent modification — retry
  }

  // Should not reach here in normal operation
  Debug::notifyError("CxlTransport: cas_mask_internal exceeded retry limit");
  *result = __atomic_load_n(static_cast<uint64_t *>(target), __ATOMIC_SEQ_CST);
  return false;
}

void CxlTransport::faa_boundary_internal(void *target, uint64_t add_val,
                                          uint64_t *result, uint64_t mask) {
  auto *ptr = static_cast<uint64_t *>(target);
  *result = __sync_fetch_and_add(ptr, add_val);
  // Apply boundary mask (matches RDMA faa_boundary semantics)
  *result &= mask;
}

// ---- Public atomic operations (main pool) ----

bool CxlTransport::cas_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                              uint64_t *rdma_buffer) {
  return cas_internal(resolve(gaddr), equal, val, rdma_buffer);
}

bool CxlTransport::cas_mask_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                                   uint64_t *rdma_buffer,
                                   uint64_t compare_mask, uint64_t swap_mask) {
  return cas_mask_internal(resolve(gaddr), equal, val, rdma_buffer,
                           compare_mask, swap_mask);
}

void CxlTransport::faa_boundary_sync(GlobalAddress gaddr, uint64_t add_val,
                                      uint64_t *rdma_buffer, uint64_t mask) {
  faa_boundary_internal(resolve(gaddr), add_val, rdma_buffer, mask);
}

// ---- On-chip memory emulation (lock region) ----

void CxlTransport::read_dm_sync(char *buffer, GlobalAddress gaddr, size_t size) {
  memcpy(buffer, resolve_lock(gaddr), size);
}

void CxlTransport::write_dm_sync(const char *buffer, GlobalAddress gaddr, size_t size) {
  memcpy(resolve_lock(gaddr), buffer, size);
}

bool CxlTransport::cas_dm_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                                 uint64_t *rdma_buffer) {
  return cas_internal(resolve_lock(gaddr), equal, val, rdma_buffer);
}

bool CxlTransport::cas_dm_mask_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                                      uint64_t *rdma_buffer,
                                      uint64_t compare_mask, uint64_t swap_mask) {
  return cas_mask_internal(resolve_lock(gaddr), equal, val, rdma_buffer,
                           compare_mask, swap_mask);
}

void CxlTransport::faa_dm_boundary_sync(GlobalAddress gaddr, uint64_t add_val,
                                          uint64_t *rdma_buffer, uint64_t mask) {
  faa_boundary_internal(resolve_lock(gaddr), add_val, rdma_buffer, mask);
}

// ---- Composite operations ----

void CxlTransport::write_cas_sync(CxlOpRegion &write_ror, CxlOpRegion &cas_ror,
                                    uint64_t equal, uint64_t val) {
  // Write first, then CAS (sequential on CXL, batched on RDMA)
  memcpy(resolve(write_ror.dest),
         reinterpret_cast<const char *>(write_ror.source), write_ror.size);
  uint64_t result;
  cas_internal(resolve(cas_ror.dest), equal, val, &result);
}

bool CxlTransport::cas_read_sync(CxlOpRegion &cas_ror, CxlOpRegion &read_ror,
                                    uint64_t equal, uint64_t val) {
  uint64_t result;
  bool success = cas_internal(resolve(cas_ror.dest), equal, val, &result);
  *reinterpret_cast<uint64_t *>(cas_ror.source) = result;
  memcpy(reinterpret_cast<char *>(read_ror.source),
         resolve(read_ror.dest), read_ror.size);
  return success;
}

bool CxlTransport::read_cas_sync(CxlOpRegion &read_ror, CxlOpRegion &cas_ror,
                                    uint64_t equal, uint64_t val) {
  memcpy(reinterpret_cast<char *>(read_ror.source),
         resolve(read_ror.dest), read_ror.size);
  uint64_t result;
  bool success = cas_internal(resolve(cas_ror.dest), equal, val, &result);
  *reinterpret_cast<uint64_t *>(cas_ror.source) = result;
  return success;
}

bool CxlTransport::cas_write_sync(CxlOpRegion &cas_ror, CxlOpRegion &write_ror,
                                    uint64_t equal, uint64_t val) {
  uint64_t result;
  bool success = cas_internal(resolve(cas_ror.dest), equal, val, &result);
  *reinterpret_cast<uint64_t *>(cas_ror.source) = result;
  memcpy(resolve(write_ror.dest),
         reinterpret_cast<const char *>(write_ror.source), write_ror.size);
  return success;
}

void CxlTransport::write_faa_sync(CxlOpRegion &write_ror, CxlOpRegion &faa_ror,
                                    uint64_t add_val) {
  memcpy(resolve(write_ror.dest),
         reinterpret_cast<const char *>(write_ror.source), write_ror.size);
  uint64_t result;
  faa_boundary_internal(resolve(faa_ror.dest), add_val, &result, 63);
  *reinterpret_cast<uint64_t *>(faa_ror.source) = result;
}

// ---- Memory management ----

GlobalAddress CxlTransport::alloc(size_t size, uint8_t align_bit) {
  uint64_t align = 1ULL << align_bit;
  uint64_t offset;

  // Atomic bump allocation with alignment
  while (true) {
    offset = alloc_offset_.load(std::memory_order_relaxed);
    uint64_t aligned = (offset + align - 1) & ~(align - 1);
    uint64_t next = aligned + size;

    if (next > pool_size_) {
      Debug::notifyError("CxlTransport: out of memory (requested %zu at offset %lu, pool=%zu)",
                         size, aligned, pool_size_);
      return GlobalAddress::Null();
    }

    if (alloc_offset_.compare_exchange_weak(offset, next, std::memory_order_relaxed)) {
      return GlobalAddress(my_node_id_, aligned);
    }
  }
}

void CxlTransport::free(const GlobalAddress &addr, int size) {
  // Simple bump allocator — no free support
  // This matches the behavior of the RDMA backend where free is rarely used
  (void)addr;
  (void)size;
}

// ---- Synchronization ----

void CxlTransport::barrier(const std::string &ss) {
  if (barrier_initialized_) {
    pthread_barrier_wait(&barrier_);
  }
  (void)ss;
}
