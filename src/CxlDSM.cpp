#ifdef USE_CXL

#include "CxlDSM.h"
#include "Debug.h"

#include <fstream>
#include <sstream>
#include <cstring>

// Thread-local storage
thread_local int CxlDSM::thread_id = -1;
thread_local uint64_t CxlDSM::thread_tag = 0;
thread_local char *CxlDSM::rdma_buffer_ = nullptr;
thread_local RdmaBuffer CxlDSM::rbuf_[MAX_CORO_NUM];

// Singleton
static CxlDSM *globalCxlDSM = nullptr;

CxlDSM *CxlDSM::getInstance(const DSMConfig &conf) {
  if (!globalCxlDSM) {
    globalCxlDSM = new CxlDSM(conf);
  }
  return globalCxlDSM;
}

CxlDSM::CxlDSM(const DSMConfig &conf)
    : conf(conf), appID(0), keySpaceSize(0) {

  // CXL pool: same size as RDMA DSM (64GB default from Common.h)
  size_t pool_size = (size_t)conf.dsmSize * define::GB;
  size_t lock_size = 128 * 1024;  // 128KB lock region (matches ON_CHIP_SIZE pages)

  Debug::notifyInfo("CxlDSM: creating transport (pool=%zuGB, lock=%zuKB, NUMA node 1)",
                    pool_size / define::GB, lock_size / 1024);

  // CXL is single-node — barrier must use 1, not machineNR (which is
  // the benchmark's node count and would deadlock the barrier)
  transport_ = new CxlTransport(1, pool_size, lock_size, 1, true);

  if (!transport_->is_initialized()) {
    Debug::notifyError("CxlDSM: transport initialization failed, trying without hugepages");
    delete transport_;
    transport_ = new CxlTransport(1, pool_size, lock_size, 1, false);
  }

  // Allocate per-thread buffers (replaces RDMA registered memory)
  size_t per_thread_buf = (size_t)define::kPerThreadRdmaBuf;
  for (int i = 0; i < MAX_APP_THREAD; i++) {
    thread_buffers_[i] = new char[per_thread_buf];
    memset(thread_buffers_[i], 0, per_thread_buf);
  }

  Debug::notifyInfo("CxlDSM initialized: pool=%zuGB, threads=%d",
                    pool_size / define::GB, conf.threadNR);
}

CxlDSM::~CxlDSM() {
  for (int i = 0; i < MAX_APP_THREAD; i++) {
    delete[] thread_buffers_[i];
  }
  delete transport_;
}

void CxlDSM::registerThread() {
  if (thread_id != -1) return;

  thread_id = appID.fetch_add(1);
  thread_tag = thread_id + 1;  // Single node, no nodeID shift

  // Set up thread-local buffer
  rdma_buffer_ = thread_buffers_[thread_id];
  for (int i = 0; i < MAX_CORO_NUM; i++) {
    rbuf_[i].set_buffer(rdma_buffer_ + i * define::kPerCoroRdmaBuf);
  }
}

void CxlDSM::loadKeySpace(const std::string &load_workloads_path, bool is_str) {
  keySpaceSize = 0;
  std::string op, line, str_k;
  int int_k;
  std::ifstream load_in(load_workloads_path);
  Debug::notifyInfo("CxlDSM: Loading key space from %s", load_workloads_path.c_str());
  while (std::getline(load_in, line)) {
    if (!line.size()) continue;
    std::istringstream tmp(line);
    tmp >> op;
    if (op != "INSERT") continue;
    if (is_str) {
      tmp >> str_k;
      keyBuffer[keySpaceSize++] = str2key(str_k);
    } else {
      tmp >> int_k;
      keyBuffer[keySpaceSize++] = int2key(int_k);
    }
    if (keySpaceSize >= MAX_KEY_SPACE_SIZE) break;
  }
  Debug::notifyInfo("CxlDSM: Key space loaded: %lu keys", keySpaceSize);
}

Key CxlDSM::getRandomKey() {
  uint32_t seed = asm_rdtsc();
  return keyBuffer[rand_r(&seed) % keySpaceSize];
}

Key CxlDSM::getNoComflictKey(uint64_t key_hash, uint64_t global_thread_id,
                              uint64_t global_thread_num) {
  auto start = keySpaceSize / global_thread_num * global_thread_id;
  return keyBuffer[start + key_hash % (keySpaceSize / global_thread_num)];
}

// ---- Batch operations (convert RdmaOpRegion to CxlTransport calls) ----
// RdmaOpRegion uses raw dest addresses; we need to reconstruct GlobalAddress from offset.

static GlobalAddress addr_from_ror(const RdmaOpRegion &ror) {
  // ror.dest is set via gaddr.to_uint64() in Tree.cpp, which packs nodeID (upper 16)
  // and offset (lower 48) into a single uint64_t. Reconstruct the GlobalAddress from
  // the packed value — CXL ignores nodeID but needs the correct offset.
  GlobalAddress ga;
  ga.val = ror.dest;
  return ga;
}

void CxlDSM::read_batch(RdmaOpRegion *rs, int k, bool signal, CoroPull *sink) {
  for (int i = 0; i < k; i++) {
    auto ga = addr_from_ror(rs[i]);
    if (rs[i].is_on_chip)
      transport_->read_dm_sync(reinterpret_cast<char *>(rs[i].source), ga, rs[i].size);
    else
      transport_->read_sync(reinterpret_cast<char *>(rs[i].source), ga, rs[i].size);
  }
}

void CxlDSM::read_batch_sync(RdmaOpRegion *rs, int k, CoroPull *sink) {
  read_batch(rs, k, true, sink);
}

void CxlDSM::read_batches_sync(const std::vector<RdmaOpRegion> &rs, CoroPull *sink) {
  for (const auto &r : rs) {
    auto ga = addr_from_ror(r);
    if (r.is_on_chip)
      transport_->read_dm_sync(reinterpret_cast<char *>(r.source), ga, r.size);
    else
      transport_->read_sync(reinterpret_cast<char *>(r.source), ga, r.size);
  }
}

void CxlDSM::write_batch(RdmaOpRegion *rs, int k, bool signal, CoroPull *sink) {
  for (int i = 0; i < k; i++) {
    auto ga = addr_from_ror(rs[i]);
    if (rs[i].is_on_chip)
      transport_->write_dm_sync(reinterpret_cast<const char *>(rs[i].source), ga, rs[i].size);
    else
      transport_->write_sync(reinterpret_cast<const char *>(rs[i].source), ga, rs[i].size);
  }
}

void CxlDSM::write_batch_sync(RdmaOpRegion *rs, int k, CoroPull *sink) {
  write_batch(rs, k, true, sink);
}

// ---- Composite operations ----

void CxlDSM::write_cas(RdmaOpRegion &write_ror, RdmaOpRegion &cas_ror,
                         uint64_t equal, uint64_t val, bool signal, CoroPull *sink) {
  transport_->write_sync(reinterpret_cast<const char *>(write_ror.source),
                         addr_from_ror(write_ror), write_ror.size);
  uint64_t result;
  transport_->cas_sync(addr_from_ror(cas_ror), equal, val, &result);
  *reinterpret_cast<uint64_t *>(cas_ror.source) = result;
}

void CxlDSM::write_cas_sync(RdmaOpRegion &write_ror, RdmaOpRegion &cas_ror,
                              uint64_t equal, uint64_t val, CoroPull *sink) {
  write_cas(write_ror, cas_ror, equal, val, true, sink);
}

bool CxlDSM::cas_read_sync(RdmaOpRegion &cas_ror, RdmaOpRegion &read_ror,
                             uint64_t equal, uint64_t val, CoroPull *sink) {
  uint64_t result;
  bool ok = transport_->cas_sync(addr_from_ror(cas_ror), equal, val, &result);
  *reinterpret_cast<uint64_t *>(cas_ror.source) = result;
  transport_->read_sync(reinterpret_cast<char *>(read_ror.source),
                        addr_from_ror(read_ror), read_ror.size);
  return ok;
}

bool CxlDSM::read_cas_sync(RdmaOpRegion &read_ror, RdmaOpRegion &cas_ror,
                             uint64_t equal, uint64_t val, CoroPull *sink) {
  transport_->read_sync(reinterpret_cast<char *>(read_ror.source),
                        addr_from_ror(read_ror), read_ror.size);
  uint64_t result;
  bool ok = transport_->cas_sync(addr_from_ror(cas_ror), equal, val, &result);
  *reinterpret_cast<uint64_t *>(cas_ror.source) = result;
  return ok;
}

bool CxlDSM::cas_write_sync(RdmaOpRegion &cas_ror, RdmaOpRegion &write_ror,
                              uint64_t equal, uint64_t val, CoroPull *sink) {
  uint64_t result;
  bool ok = transport_->cas_sync(addr_from_ror(cas_ror), equal, val, &result);
  *reinterpret_cast<uint64_t *>(cas_ror.source) = result;
  transport_->write_sync(reinterpret_cast<const char *>(write_ror.source),
                         addr_from_ror(write_ror), write_ror.size);
  return ok;
}

void CxlDSM::write_faa(RdmaOpRegion &write_ror, RdmaOpRegion &faa_ror,
                         uint64_t add_val, bool signal, CoroPull *sink) {
  transport_->write_sync(reinterpret_cast<const char *>(write_ror.source),
                         addr_from_ror(write_ror), write_ror.size);
  uint64_t result;
  transport_->faa_boundary_sync(addr_from_ror(faa_ror), add_val, &result, 63);
  *reinterpret_cast<uint64_t *>(faa_ror.source) = result;
}

void CxlDSM::write_faa_sync(RdmaOpRegion &write_ror, RdmaOpRegion &faa_ror,
                              uint64_t add_val, CoroPull *sink) {
  write_faa(write_ror, faa_ror, add_val, true, sink);
}

#endif /* USE_CXL */
