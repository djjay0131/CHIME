#ifndef __CXL_TRANSPORT_H__
#define __CXL_TRANSPORT_H__

/**
 * CxlTransport — CXL-emulated transport backend for CHIME.
 *
 * Replaces RDMA one-sided operations with CPU load/store on NUMA-emulated
 * CXL memory. Uses mmap with MPOL_BIND to a remote NUMA node to simulate
 * CXL Type 3 memory. Atomic operations use GCC builtins.
 *
 * No coroutines, no memory registration, no completion queues — all
 * operations are synchronous CPU instructions.
 *
 * Build with: cmake -DUSE_CXL=ON ..
 */

#include "GlobalAddress.h"
#include "Common.h"

#include <atomic>
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <string>
#include <pthread.h>

// Transport-agnostic operation region (replaces RdmaOpRegion for CXL path)
struct CxlOpRegion {
  uint64_t source;      // local buffer address
  GlobalAddress dest;   // remote address (only offset used in CXL)
  uint64_t size;
};

class CxlTransport {
public:
  /**
   * Initialize CXL transport with NUMA-emulated memory.
   *
   * @param numa_node  NUMA node to bind memory to (typically 1 for remote)
   * @param pool_size  Size of main memory pool in bytes
   * @param lock_size  Size of lock memory region in bytes (emulates on-chip memory)
   * @param machine_nr Total number of machines (for barrier coordination)
   * @param use_hugepages Whether to use hugepages for the memory pool
   */
  CxlTransport(int numa_node, size_t pool_size, size_t lock_size,
                int machine_nr = 1, bool use_hugepages = true);
  ~CxlTransport();

  // Prevent copy
  CxlTransport(const CxlTransport&) = delete;
  CxlTransport& operator=(const CxlTransport&) = delete;

  // ---- One-sided read/write (synchronous, no coroutines) ----

  void read_sync(char *buffer, GlobalAddress gaddr, size_t size);
  void write_sync(const char *buffer, GlobalAddress gaddr, size_t size);

  // ---- Batch operations ----

  void read_batch_sync(CxlOpRegion *rs, int count);
  void write_batch_sync(CxlOpRegion *rs, int count);

  // ---- Atomic operations ----

  // Compare-and-swap: returns true if swap succeeded
  bool cas_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                uint64_t *rdma_buffer);

  // Masked compare-and-swap (emulates Mellanox IBV_EXP_WR_EXT_MASKED_ATOMIC_CMP_AND_SWP)
  // Uses read-modify-CAS loop. swap_mask must contain compare_mask.
  bool cas_mask_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                     uint64_t *rdma_buffer,
                     uint64_t compare_mask = ~(0ull),
                     uint64_t swap_mask = ~(0ull));

  // Fetch-and-add with boundary mask
  void faa_boundary_sync(GlobalAddress gaddr, uint64_t add_val,
                         uint64_t *rdma_buffer, uint64_t mask = 63);

  // ---- On-chip memory emulation (lock region) ----

  void read_dm_sync(char *buffer, GlobalAddress gaddr, size_t size);
  void write_dm_sync(const char *buffer, GlobalAddress gaddr, size_t size);
  bool cas_dm_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                   uint64_t *rdma_buffer);
  bool cas_dm_mask_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                        uint64_t *rdma_buffer,
                        uint64_t compare_mask = ~(0ull),
                        uint64_t swap_mask = ~(0ull));
  void faa_dm_boundary_sync(GlobalAddress gaddr, uint64_t add_val,
                            uint64_t *rdma_buffer, uint64_t mask = 63);

  // ---- Composite operations (sequential on CXL, batched on RDMA) ----

  void write_cas_sync(CxlOpRegion &write_ror, CxlOpRegion &cas_ror,
                      uint64_t equal, uint64_t val);
  bool cas_read_sync(CxlOpRegion &cas_ror, CxlOpRegion &read_ror,
                     uint64_t equal, uint64_t val);
  bool read_cas_sync(CxlOpRegion &read_ror, CxlOpRegion &cas_ror,
                     uint64_t equal, uint64_t val);
  bool cas_write_sync(CxlOpRegion &cas_ror, CxlOpRegion &write_ror,
                      uint64_t equal, uint64_t val);
  void write_faa_sync(CxlOpRegion &write_ror, CxlOpRegion &faa_ror,
                      uint64_t add_val);

  // ---- Memory management ----

  GlobalAddress alloc(size_t size, uint8_t align_bit = CACHELINE_ALIGN_BIT);
  void free(const GlobalAddress &addr, int size);

  // ---- Synchronization ----

  void barrier(const std::string &ss);

  // ---- Node identity ----

  uint16_t getMyNodeID() const { return my_node_id_; }
  uint16_t getClusterSize() const { return machine_nr_; }

  // ---- Direct memory access (for testing/debugging) ----

  void *get_base_addr() const { return base_addr_; }
  void *get_lock_addr() const { return lock_addr_; }
  size_t get_pool_size() const { return pool_size_; }
  size_t get_lock_size() const { return lock_size_; }
  bool is_initialized() const { return base_addr_ != nullptr; }

private:
  // Resolve a GlobalAddress to a pointer in the memory pool
  void *resolve(GlobalAddress gaddr) const {
    return static_cast<char *>(base_addr_) + gaddr.offset;
  }

  // Resolve a GlobalAddress to a pointer in the lock region
  void *resolve_lock(GlobalAddress gaddr) const {
    return static_cast<char *>(lock_addr_) + gaddr.offset;
  }

  // Internal CAS implementation (shared between regular and lock regions)
  bool cas_internal(void *target, uint64_t equal, uint64_t val,
                    uint64_t *result);
  bool cas_mask_internal(void *target, uint64_t equal, uint64_t val,
                         uint64_t *result,
                         uint64_t compare_mask, uint64_t swap_mask);
  void faa_boundary_internal(void *target, uint64_t add_val,
                             uint64_t *result, uint64_t mask);

  void *base_addr_;     // Main memory pool (mmap'd to remote NUMA node)
  void *lock_addr_;     // Lock region (emulates on-chip NIC memory)
  size_t pool_size_;    // Size of main memory pool
  size_t lock_size_;    // Size of lock region
  int numa_node_;       // NUMA node the memory is bound to
  int machine_nr_;      // Number of machines (for barrier)
  uint16_t my_node_id_; // This node's ID (always 0 for CXL single-node)

  // Simple bump allocator for CXL memory
  std::atomic<uint64_t> alloc_offset_;

  // Barrier state
  pthread_barrier_t barrier_;
  bool barrier_initialized_;
};

#endif /* __CXL_TRANSPORT_H__ */
