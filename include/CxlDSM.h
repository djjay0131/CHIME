#ifndef __CXL_DSM_H__
#define __CXL_DSM_H__

/**
 * CxlDSM — Drop-in replacement for DSM that uses CXL (NUMA-emulated) transport.
 *
 * Presents the same public interface as DSM so that Tree.cpp and ycsb_test.cpp
 * can use it without modification. Internally uses CxlTransport for all memory
 * operations instead of RDMA.
 *
 * Usage: #ifdef USE_CXL, create CxlDSM instead of DSM.
 * The pointer type remains DSM* via inheritance or the preprocessor.
 *
 * Key differences from DSM:
 *   - No RDMA, no memcached, no coroutines
 *   - Memory is local NUMA (node 1), not remote via network
 *   - Synchronous operations only (no async/polling)
 *   - Single-node only (no multi-node coordination)
 *   - get_rbuf returns a local buffer (no RDMA registration)
 */

#ifdef USE_CXL

#include "CxlTransport.h"
#include "GlobalAddress.h"
#include "Common.h"
#include "Config.h"
#include "RdmaBuffer.h"

#include <atomic>
#include <cstring>
#include <string>
#include <fstream>
#include <sstream>
#include <iostream>

// RdmaOpRegion is defined in Common.h (CXL-mode stub version)
// RawMessage forward-declared here (only used in no-op RPC stubs)
struct RawMessage;

class CxlDSM {
public:
  static CxlDSM *getInstance(const DSMConfig &conf);

  void registerThread();
  void loadKeySpace(const std::string &load_workloads_path, bool is_str);
  Key getRandomKey();
  Key getNoComflictKey(uint64_t key_hash, uint64_t global_thread_id,
                       uint64_t global_thread_num);

  uint16_t getMyNodeID() { return 0; }  // Always node 0 for CXL
  uint16_t getMyThreadID() { return thread_id; }
  uint16_t getClusterSize() { return 1; }  // Single node
  uint64_t getThreadTag() { return thread_tag; }
  uint64_t getMyGlobalThreadID() { return thread_id - 1; }

  // ---- RDMA-compatible read/write (delegates to CxlTransport) ----

  void read(char *buffer, GlobalAddress gaddr, size_t size, bool signal = true,
            CoroPull *sink = nullptr) {
    transport_->read_sync(buffer, gaddr, size);
  }
  void read_sync(char *buffer, GlobalAddress gaddr, size_t size,
                 CoroPull *sink = nullptr) {
    transport_->read_sync(buffer, gaddr, size);
  }

  void write(const char *buffer, GlobalAddress gaddr, size_t size,
             bool signal = true, CoroPull *sink = nullptr) {
    transport_->write_sync(buffer, gaddr, size);
  }
  void write_sync(const char *buffer, GlobalAddress gaddr, size_t size,
                  CoroPull *sink = nullptr) {
    transport_->write_sync(buffer, gaddr, size);
  }

  // Batch operations — convert RdmaOpRegion to CxlOpRegion
  void read_batch(RdmaOpRegion *rs, int k, bool signal = true,
                  CoroPull *sink = nullptr);
  void read_batch_sync(RdmaOpRegion *rs, int k, CoroPull *sink = nullptr);
  void read_batches_sync(const std::vector<RdmaOpRegion> &rs,
                         CoroPull *sink = nullptr);

  void write_batch(RdmaOpRegion *rs, int k, bool signal = true,
                   CoroPull *sink = nullptr);
  void write_batch_sync(RdmaOpRegion *rs, int k, CoroPull *sink = nullptr);

  // ---- Atomic operations ----

  void cas(GlobalAddress gaddr, uint64_t equal, uint64_t val,
           uint64_t *rdma_buffer, bool signal = true,
           CoroPull *sink = nullptr) {
    transport_->cas_sync(gaddr, equal, val, rdma_buffer);
  }
  bool cas_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                uint64_t *rdma_buffer, CoroPull *sink = nullptr) {
    return transport_->cas_sync(gaddr, equal, val, rdma_buffer);
  }

  bool cas_mask_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                     uint64_t *rdma_buffer, uint64_t compare_mask = ~(0ull),
                     uint64_t swap_mask = ~(0ull),
                     CoroPull *sink = nullptr) {
    return transport_->cas_mask_sync(gaddr, equal, val, rdma_buffer,
                                     compare_mask, swap_mask);
  }

  void faa_boundary(GlobalAddress gaddr, uint64_t add_val,
                    uint64_t *rdma_buffer, uint64_t mask = 63,
                    bool signal = true, CoroPull *sink = nullptr) {
    transport_->faa_boundary_sync(gaddr, add_val, rdma_buffer, mask);
  }
  void faa_boundary_sync(GlobalAddress gaddr, uint64_t add_val,
                         uint64_t *rdma_buffer, uint64_t mask = 63,
                         CoroPull *sink = nullptr) {
    transport_->faa_boundary_sync(gaddr, add_val, rdma_buffer, mask);
  }

  // ---- On-chip memory emulation ----

  void read_dm(char *buffer, GlobalAddress gaddr, size_t size,
               bool signal = true, CoroPull *sink = nullptr) {
    transport_->read_dm_sync(buffer, gaddr, size);
  }
  void read_dm_sync(char *buffer, GlobalAddress gaddr, size_t size,
                    CoroPull *sink = nullptr) {
    transport_->read_dm_sync(buffer, gaddr, size);
  }

  void write_dm(const char *buffer, GlobalAddress gaddr, size_t size,
                bool signal = true, CoroPull *sink = nullptr) {
    transport_->write_dm_sync(buffer, gaddr, size);
  }
  void write_dm_sync(const char *buffer, GlobalAddress gaddr, size_t size,
                     CoroPull *sink = nullptr) {
    transport_->write_dm_sync(buffer, gaddr, size);
  }

  bool cas_dm_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                   uint64_t *rdma_buffer, CoroPull *sink = nullptr) {
    return transport_->cas_dm_sync(gaddr, equal, val, rdma_buffer);
  }

  bool cas_dm_mask_sync(GlobalAddress gaddr, uint64_t equal, uint64_t val,
                        uint64_t *rdma_buffer,
                        uint64_t compare_mask = ~(0ull),
                        uint64_t swap_mask = ~(0ull),
                        CoroPull *sink = nullptr) {
    return transport_->cas_dm_mask_sync(gaddr, equal, val, rdma_buffer,
                                        compare_mask, swap_mask);
  }

  void faa_dm_boundary(GlobalAddress gaddr, uint64_t add_val,
                       uint64_t *rdma_buffer, uint64_t mask = 63,
                       bool signal = true, CoroPull *sink = nullptr) {
    transport_->faa_dm_boundary_sync(gaddr, add_val, rdma_buffer, mask);
  }
  void faa_dm_boundary_sync(GlobalAddress gaddr, uint64_t add_val,
                            uint64_t *rdma_buffer, uint64_t mask = 63,
                            CoroPull *sink = nullptr) {
    transport_->faa_dm_boundary_sync(gaddr, add_val, rdma_buffer, mask);
  }

  // ---- Composite operations ----

  void write_cas(RdmaOpRegion &write_ror, RdmaOpRegion &cas_ror,
                 uint64_t equal, uint64_t val, bool signal = true,
                 CoroPull *sink = nullptr);
  void write_cas_sync(RdmaOpRegion &write_ror, RdmaOpRegion &cas_ror,
                      uint64_t equal, uint64_t val, CoroPull *sink = nullptr);

  bool cas_read_sync(RdmaOpRegion &cas_ror, RdmaOpRegion &read_ror,
                     uint64_t equal, uint64_t val, CoroPull *sink = nullptr);
  bool read_cas_sync(RdmaOpRegion &read_ror, RdmaOpRegion &cas_ror,
                     uint64_t equal, uint64_t val, CoroPull *sink = nullptr);
  bool cas_write_sync(RdmaOpRegion &cas_ror, RdmaOpRegion &write_ror,
                      uint64_t equal, uint64_t val, CoroPull *sink = nullptr);

  void write_faa(RdmaOpRegion &write_ror, RdmaOpRegion &faa_ror,
                 uint64_t add_val, bool signal = true,
                 CoroPull *sink = nullptr);
  void write_faa_sync(RdmaOpRegion &write_ror, RdmaOpRegion &faa_ror,
                      uint64_t add_val, CoroPull *sink = nullptr);

  // ---- CQ polling (no-op for CXL, all operations are synchronous) ----

  uint64_t poll_rdma_cq(int count = 1) { return 0; }
  bool poll_rdma_cq_once(uint64_t &wr_id) { return true; }

  // ---- Coordination ----

  uint64_t sum(uint64_t value) { return value; }  // Single node, just return
  void barrier(const std::string &ss) { transport_->barrier(ss); }

  bool is_register() { return thread_id != -1; }
  char *get_rdma_buffer() { return rdma_buffer_; }
  RdmaBuffer &get_rbuf(CoroPull *sink) { return rbuf_[0]; }

  // ---- Memory management ----

  GlobalAddress alloc(size_t size, uint8_t align_bit = CACHELINE_ALIGN_BIT) {
    return transport_->alloc(size, align_bit);
  }
  void free(const GlobalAddress &addr, int size) {
    transport_->free(addr, size);
  }

  // Stubs for RPC (not used in CXL mode)
  void rpc_call_dir(const RawMessage &m, uint16_t node_id,
                    uint16_t dir_id = 0) {}
  RawMessage *rpc_wait() { return nullptr; }

  // Expose Put/Get for memcached-less coordination
  size_t Put(uint64_t key, const void *value, size_t count) { return count; }
  size_t Get(uint64_t key, void *value) { return 0; }

private:
  CxlDSM(const DSMConfig &conf);
  ~CxlDSM();

  CxlTransport *transport_;
  DSMConfig conf;
  std::atomic_int appID;

  static thread_local int thread_id;
  static thread_local uint64_t thread_tag;
  static thread_local char *rdma_buffer_;
  static thread_local RdmaBuffer rbuf_[MAX_CORO_NUM];

  uint64_t keySpaceSize;
  Key keyBuffer[MAX_KEY_SPACE_SIZE];

  // Per-thread local buffer (replaces RDMA registered memory)
  char *thread_buffers_[MAX_APP_THREAD];
};

// Preprocessor alias: when USE_CXL is defined, "DSM" refers to CxlDSM
#define DSM CxlDSM

#endif /* USE_CXL */

#endif /* __CXL_DSM_H__ */
