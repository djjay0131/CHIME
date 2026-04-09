/**
 * test_cxl_transport.cpp — Unit tests for CxlTransport.
 *
 * Tests the CXL transport backend in isolation (no RDMA, no cluster).
 * Uses anonymous mmap (no hugepages) so it runs on any Linux machine.
 *
 * Build: cmake -DUSE_CXL=ON .. && make test_cxl_transport
 * Run:   ./test_cxl_transport
 */

#include "CxlTransport.h"

#include <cassert>
#include <cstdio>
#include <cstring>
#include <thread>
#include <vector>
#include <atomic>

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) \
  do { printf("  %-50s ", #name); } while (0)

#define PASS() \
  do { printf("PASS\n"); tests_passed++; } while (0)

#define FAIL(msg) \
  do { printf("FAIL: %s\n", msg); tests_failed++; } while (0)

#define ASSERT_EQ(a, b, msg) \
  do { if ((a) != (b)) { FAIL(msg); return; } } while (0)

#define ASSERT_TRUE(x, msg) \
  do { if (!(x)) { FAIL(msg); return; } } while (0)

// ---- Test: Initialization ----

void test_init_succeeds() {
  TEST(init_succeeds);
  // Use small pool without hugepages for local testing
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);
  ASSERT_TRUE(t.is_initialized(), "transport should be initialized");
  ASSERT_EQ(t.get_pool_size(), 1024UL * 1024, "pool size mismatch");
  ASSERT_EQ(t.get_lock_size(), 4096UL, "lock size mismatch");
  ASSERT_EQ(t.getMyNodeID(), 0, "node ID should be 0");
  PASS();
}

// ---- Test: Read/Write ----

void test_write_then_read() {
  TEST(write_then_read);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  const char *data = "hello CXL";
  GlobalAddress addr(0, 0);
  t.write_sync(data, addr, strlen(data) + 1);

  char buf[64] = {0};
  t.read_sync(buf, addr, strlen(data) + 1);
  ASSERT_EQ(strcmp(buf, "hello CXL"), 0, "read data should match written data");
  PASS();
}

void test_write_at_offset() {
  TEST(write_at_offset);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t val1 = 0xDEADBEEF;
  uint64_t val2 = 0xCAFEBABE;
  GlobalAddress addr1(0, 0);
  GlobalAddress addr2(0, 64);

  t.write_sync(reinterpret_cast<const char *>(&val1), addr1, sizeof(val1));
  t.write_sync(reinterpret_cast<const char *>(&val2), addr2, sizeof(val2));

  uint64_t r1, r2;
  t.read_sync(reinterpret_cast<char *>(&r1), addr1, sizeof(r1));
  t.read_sync(reinterpret_cast<char *>(&r2), addr2, sizeof(r2));

  ASSERT_EQ(r1, 0xDEADBEEFULL, "first value mismatch");
  ASSERT_EQ(r2, 0xCAFEBABEULL, "second value mismatch");
  PASS();
}

void test_nodeid_ignored() {
  TEST(nodeid_ignored_in_resolve);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t val = 42;
  GlobalAddress addr_node0(0, 128);
  GlobalAddress addr_node5(5, 128);  // Different nodeID, same offset

  t.write_sync(reinterpret_cast<const char *>(&val), addr_node0, sizeof(val));

  uint64_t result;
  t.read_sync(reinterpret_cast<char *>(&result), addr_node5, sizeof(result));
  ASSERT_EQ(result, 42ULL, "nodeID should be ignored; same offset = same memory");
  PASS();
}

// ---- Test: Batch Operations ----

void test_read_batch() {
  TEST(read_batch_sync);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t v1 = 100, v2 = 200;
  t.write_sync(reinterpret_cast<const char *>(&v1), GlobalAddress(0, 0), 8);
  t.write_sync(reinterpret_cast<const char *>(&v2), GlobalAddress(0, 64), 8);

  uint64_t r1, r2;
  CxlOpRegion ops[2];
  ops[0] = {reinterpret_cast<uint64_t>(&r1), GlobalAddress(0, 0), 8};
  ops[1] = {reinterpret_cast<uint64_t>(&r2), GlobalAddress(0, 64), 8};

  t.read_batch_sync(ops, 2);
  ASSERT_EQ(r1, 100ULL, "batch read[0] mismatch");
  ASSERT_EQ(r2, 200ULL, "batch read[1] mismatch");
  PASS();
}

void test_write_batch() {
  TEST(write_batch_sync);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t v1 = 300, v2 = 400;
  CxlOpRegion ops[2];
  ops[0] = {reinterpret_cast<uint64_t>(&v1), GlobalAddress(0, 0), 8};
  ops[1] = {reinterpret_cast<uint64_t>(&v2), GlobalAddress(0, 64), 8};

  t.write_batch_sync(ops, 2);

  uint64_t r1, r2;
  t.read_sync(reinterpret_cast<char *>(&r1), GlobalAddress(0, 0), 8);
  t.read_sync(reinterpret_cast<char *>(&r2), GlobalAddress(0, 64), 8);
  ASSERT_EQ(r1, 300ULL, "batch write[0] mismatch");
  ASSERT_EQ(r2, 400ULL, "batch write[1] mismatch");
  PASS();
}

// ---- Test: CAS ----

void test_cas_success() {
  TEST(cas_sync_success);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t initial = 10;
  GlobalAddress addr(0, 0);
  t.write_sync(reinterpret_cast<const char *>(&initial), addr, 8);

  uint64_t result;
  bool ok = t.cas_sync(addr, 10, 20, &result);
  ASSERT_TRUE(ok, "CAS should succeed when equal matches");
  ASSERT_EQ(result, 10ULL, "CAS result should be old value");

  uint64_t check;
  t.read_sync(reinterpret_cast<char *>(&check), addr, 8);
  ASSERT_EQ(check, 20ULL, "value should be updated to 20");
  PASS();
}

void test_cas_failure() {
  TEST(cas_sync_failure);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t initial = 10;
  GlobalAddress addr(0, 0);
  t.write_sync(reinterpret_cast<const char *>(&initial), addr, 8);

  uint64_t result;
  bool ok = t.cas_sync(addr, 99, 20, &result);  // 99 != 10
  ASSERT_TRUE(!ok, "CAS should fail when equal doesn't match");
  ASSERT_EQ(result, 10ULL, "CAS result should be current value");

  uint64_t check;
  t.read_sync(reinterpret_cast<char *>(&check), addr, 8);
  ASSERT_EQ(check, 10ULL, "value should be unchanged");
  PASS();
}

// ---- Test: Masked CAS ----

void test_cas_mask_success() {
  TEST(cas_mask_sync_success);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  // Bit 63 = lock bit, lower bits = data
  uint64_t initial = 0x00000000DEADBEEF;  // lock bit clear
  GlobalAddress addr(0, 0);
  t.write_sync(reinterpret_cast<const char *>(&initial), addr, 8);

  uint64_t result;
  uint64_t lock_bit = 1ULL << 63;
  // Try to set lock bit (compare mask = lock bit, swap mask = lock bit)
  bool ok = t.cas_mask_sync(addr, 0, lock_bit, &result, lock_bit, lock_bit);
  ASSERT_TRUE(ok, "masked CAS should succeed (lock bit was 0)");

  uint64_t check;
  t.read_sync(reinterpret_cast<char *>(&check), addr, 8);
  ASSERT_TRUE((check & lock_bit) != 0, "lock bit should be set");
  ASSERT_EQ(check & ~lock_bit, 0x00000000DEADBEEFULL, "data bits should be preserved");
  PASS();
}

void test_cas_mask_failure() {
  TEST(cas_mask_sync_failure);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t lock_bit = 1ULL << 63;
  uint64_t initial = lock_bit | 0xCAFE;  // lock bit already set
  GlobalAddress addr(0, 0);
  t.write_sync(reinterpret_cast<const char *>(&initial), addr, 8);

  uint64_t result;
  // Try to acquire lock (expect lock bit = 0, but it's 1)
  bool ok = t.cas_mask_sync(addr, 0, lock_bit, &result, lock_bit, lock_bit);
  ASSERT_TRUE(!ok, "masked CAS should fail (lock bit already set)");
  PASS();
}

// ---- Test: FAA ----

void test_faa_boundary() {
  TEST(faa_boundary_sync);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t initial = 5;
  GlobalAddress addr(0, 0);
  t.write_sync(reinterpret_cast<const char *>(&initial), addr, 8);

  uint64_t result;
  t.faa_boundary_sync(addr, 3, &result, 63);
  ASSERT_EQ(result, 5ULL & 63, "FAA result should be old value masked");

  uint64_t check;
  t.read_sync(reinterpret_cast<char *>(&check), addr, 8);
  ASSERT_EQ(check, 8ULL, "value should be 5 + 3 = 8");
  PASS();
}

// ---- Test: Lock Region (on-chip memory emulation) ----

void test_dm_read_write() {
  TEST(dm_read_write_sync);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t val = 0xFEEDFACE;
  GlobalAddress addr(0, 0);
  t.write_dm_sync(reinterpret_cast<const char *>(&val), addr, 8);

  uint64_t result;
  t.read_dm_sync(reinterpret_cast<char *>(&result), addr, 8);
  ASSERT_EQ(result, 0xFEEDFACEULL, "DM read should match DM write");
  PASS();
}

void test_dm_cas() {
  TEST(dm_cas_sync);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t initial = 100;
  GlobalAddress addr(0, 0);
  t.write_dm_sync(reinterpret_cast<const char *>(&initial), addr, 8);

  uint64_t result;
  bool ok = t.cas_dm_sync(addr, 100, 200, &result);
  ASSERT_TRUE(ok, "DM CAS should succeed");
  ASSERT_EQ(result, 100ULL, "DM CAS result should be old value");
  PASS();
}

// ---- Test: Memory Allocation ----

void test_alloc_sequential() {
  TEST(alloc_sequential);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  GlobalAddress a1 = t.alloc(64, 6);  // 64-byte aligned
  GlobalAddress a2 = t.alloc(64, 6);
  GlobalAddress a3 = t.alloc(128, 6);

  ASSERT_TRUE(a1 != GlobalAddress::Null(), "first alloc should succeed");
  ASSERT_TRUE(a2 != GlobalAddress::Null(), "second alloc should succeed");
  ASSERT_TRUE(a3 != GlobalAddress::Null(), "third alloc should succeed");
  ASSERT_TRUE(a1.offset != a2.offset, "allocations should not overlap");
  ASSERT_TRUE(a2.offset != a3.offset, "allocations should not overlap");
  ASSERT_EQ(a1.offset % 64, 0ULL, "allocation should be 64-byte aligned");
  ASSERT_EQ(a2.offset % 64, 0ULL, "allocation should be 64-byte aligned");
  PASS();
}

// ---- Test: Composite Operations ----

void test_write_cas_sync() {
  TEST(write_cas_sync);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t data_val = 0xABCD;
  uint64_t cas_initial = 10;
  GlobalAddress data_addr(0, 0);
  GlobalAddress cas_addr(0, 64);

  t.write_sync(reinterpret_cast<const char *>(&cas_initial), cas_addr, 8);

  CxlOpRegion write_ror = {reinterpret_cast<uint64_t>(&data_val), data_addr, 8};
  CxlOpRegion cas_ror = {0, cas_addr, 8};

  t.write_cas_sync(write_ror, cas_ror, 10, 20);

  uint64_t check_data, check_cas;
  t.read_sync(reinterpret_cast<char *>(&check_data), data_addr, 8);
  t.read_sync(reinterpret_cast<char *>(&check_cas), cas_addr, 8);
  ASSERT_EQ(check_data, 0xABCDULL, "data should be written");
  ASSERT_EQ(check_cas, 20ULL, "CAS should have updated");
  PASS();
}

// ---- Test: Concurrent CAS (stress test) ----

void test_concurrent_cas() {
  TEST(concurrent_cas_no_lost_updates);
  CxlTransport t(0, 1024 * 1024, 4096, 1, false);

  uint64_t initial = 0;
  GlobalAddress addr(0, 0);
  t.write_sync(reinterpret_cast<const char *>(&initial), addr, 8);

  const int NUM_THREADS = 4;
  const int INCREMENTS = 10000;
  std::vector<std::thread> threads;

  for (int i = 0; i < NUM_THREADS; i++) {
    threads.emplace_back([&t, addr]() {
      for (int j = 0; j < INCREMENTS; j++) {
        uint64_t result;
        while (true) {
          uint64_t current;
          t.read_sync(reinterpret_cast<char *>(&current), addr, 8);
          if (t.cas_sync(addr, current, current + 1, &result)) {
            break;
          }
        }
      }
    });
  }

  for (auto &th : threads) th.join();

  uint64_t final_val;
  t.read_sync(reinterpret_cast<char *>(&final_val), addr, 8);
  ASSERT_EQ(final_val, (uint64_t)(NUM_THREADS * INCREMENTS),
            "final value should equal total increments");
  PASS();
}

// ---- Main ----

int main() {
  printf("=== CxlTransport Unit Tests ===\n\n");

  // Initialization
  test_init_succeeds();

  // Read/Write
  test_write_then_read();
  test_write_at_offset();
  test_nodeid_ignored();

  // Batch
  test_read_batch();
  test_write_batch();

  // CAS
  test_cas_success();
  test_cas_failure();

  // Masked CAS
  test_cas_mask_success();
  test_cas_mask_failure();

  // FAA
  test_faa_boundary();

  // Lock region (on-chip emulation)
  test_dm_read_write();
  test_dm_cas();

  // Allocation
  test_alloc_sequential();

  // Composite
  test_write_cas_sync();

  // Concurrency
  test_concurrent_cas();

  printf("\n=== Results: %d passed, %d failed ===\n",
         tests_passed, tests_failed);
  return tests_failed > 0 ? 1 : 0;
}
