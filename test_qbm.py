"""
Tests unitaires QBM v1.1
Exécution: python test_qbm.py
"""
import unittest
from qbm import QBM, QBMAssembler

class TestQBMAssembler(unittest.TestCase):
    def setUp(self):
        self.a = QBMAssembler()

    def test_hello_world(self):
        bc = self.a.assemble("""
            MOV R0, @msg
            MOV R1, #16
            CALL CONSOLE_OUT
            CALL HALT
        msg:
            .ascii "Hello, Silicium!"
        """)
        self.assertGreater(len(bc), 5)
        vm = QBM()
        vm.load(bc)
        steps = vm.run()
        self.assertGreater(steps, 0)

    def test_addition(self):
        bc = self.a.assemble("""
            MOV R0, #42
            MOV R1, #58
            ADD R0, R1
            CALL HALT
        """)
        vm = QBM()
        vm.load(bc)
        vm.run()
        self.assertEqual(vm.regs[0], 100)

    def test_comparison(self):
        bc = self.a.assemble("""
            MOV R0, #100
            MOV R1, #200
            CMP R0, R1
            CALL HALT
        """)
        vm = QBM()
        vm.load(bc)
        vm.run()
        self.assertTrue(vm.flags & 0x04)  # FLAG_C (R0 < R1)

    def test_human_alias(self):
        bc = self.a.assemble("""
            PRINT @msg, #5
            STOP
        msg:
            .ascii "HELLO"
        """)
        self.assertGreater(len(bc), 3)

    def test_human_reg_alias(self):
        bc = self.a.assemble("""
            MOVE result, #99
            STOP
        """)
        vm = QBM()
        vm.load(bc)
        vm.run()
        self.assertEqual(vm.regs[0], 99)

    def test_hash_sha256(self):
        bc = self.a.assemble("""
            MOV R0, @data
            MOV R1, #4
            MOV R2, @hash_out
            CALL HASH_SHA256
            CALL HALT
        data:
            .byte 0xde,0xad,0xbe,0xef
        """ + "hash_out:\n" + " " * 100)
        # Note: hash_out area needs space; this assembles but test is structural
        self.assertGreater(len(bc), 10)

    def test_p2p_send(self):
        bc = self.a.assemble("""
            MOV R0, @dest
            MOV R1, @msg
            MOV R2, #5
            CALL P2P_SEND
            CALL HALT
        dest:
            .ascii "alice"
        msg:
            .ascii "50EUR"
        """)
        vm = QBM()
        vm.load(bc)
        vm.run()
        self.assertEqual(len(vm.p2p_inbox), 1)
        self.assertEqual(vm.p2p_inbox[0][1], b"50EUR")

    def test_mnemonic_resolution(self):
        """Tous les alias mnémoniques se résolvent"""
        aliases = [
            ('MOVE R0, #1', None),
            ('PUT R0, #1', None),
            ('SET R0, #1', None),
            ('INVOKE HALT', None),
            ('DO HALT', None),
            ('STOP', None),
            ('END', None),
        ]
        for source, _ in aliases:
            try:
                bc = self.a.assemble(source + "\n")
                self.assertGreater(len(bc), 0, f"Failed: {source}")
            except Exception as e:
                self.fail(f"{source}: {e}")

class TestQBMIntegration(unittest.TestCase):
    def test_full_cycle(self):
        """Assemble + execute + verify"""
        a = QBMAssembler()
        bc = a.assemble("""
            MOV R0, #10
            MOV R1, #15
            ADD R0, R1
            MOV R2, R0
            CMP R2, #25
            JMP 1, ok
            MOV R0, #0
            CALL HALT
        ok:
            MOV R0, #1
            CALL HALT
        """)
        vm = QBM()
        vm.load(bc)
        vm.run()
        self.assertEqual(vm.regs[0], 1)

if __name__ == '__main__':
    unittest.main()
