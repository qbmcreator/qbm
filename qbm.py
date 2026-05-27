
"""
QBM - Quantum BareMetal Virtual Machine
Le coeur qui bat. 7 instructions + 3 appels semantiques. Silicium nu.
"""
import sys, hashlib, os, time as time_module, math

# Lazy-load du modele d'embedding (80 Mo, charge une seule fois)
_st_model = None
def _get_st_model():
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _st_model

MEM_SIZE = 65536
NUM_REGS = 16
FLAG_Z, FLAG_C, FLAG_N = 1, 2, 4
R_SP, R_PC = 14, 15

OP_MOV=0x01; OP_ADD=0x02; OP_CMP=0x03; OP_JMP=0x04
OP_CALL=0x05; OP_LOAD=0x06; OP_STOR=0x07

MODE_REG=0x00; MODE_IMM8=0x10; MODE_IMM16=0x11
MODE_IMM32=0x12; MODE_MEM_REG=0x20; MODE_MEM_ABS=0x30

NATIVE_NAMES = {0x00:"HALT",0x01:"CONSOLE_OUT",0x02:"CONSOLE_IN",
    0x03:"HASH_SHA256",0x04:"ED25519_SIGN",0x05:"ED25519_VERIFY",
    0x06:"P2P_SEND",0x07:"P2P_RECV",0x08:"RANDOM",
    0x09:"TIME",0x0A:"EMBED_TEXT",0x0B:"COSINE_SIM",
    0x0C:"LOAD_MODEL",
    0x0E:"DEBUG_REG",0x0F:"DEBUG_MEM"}

# Alias mnemoniques pour QBM Human (lisibilite non-codeur)
# Resolus avant la table d'opcodes standard — bytecode identique
MNEMONIC_ALIASES = {
    # Instructions
    'MOVE':'MOV', 'PUT':'MOV', 'SET':'MOV', 'COPY':'MOV',
    'COMPARE':'CMP', 'CHECK':'CMP', 'TEST':'CMP', 'IS':'CMP',
    'JUMP':'JMP', 'GOTO':'JMP', 'SKIP':'JMP',
    'ADD_TO':'ADD', 'INCREASE':'ADD', 'PLUS':'ADD',
    'INVOKE':'CALL', 'DO':'CALL', 'EXECUTE':'CALL', 'RUN':'CALL',
    'READ':'LOAD', 'FETCH':'LOAD', 'GET':'LOAD',
    'WRITE':'STOR', 'SAVE':'STOR', 'STORE':'STOR', 'REMEMBER':'STOR',
    # Appels natifs
    'PRINT':'CONSOLE_OUT', 'DISPLAY':'CONSOLE_OUT', 'SAY':'CONSOLE_OUT',
    'HASH':'HASH_SHA256', 'SIGN':'ED25519_SIGN',
    'VERIFY_SIGNATURE':'ED25519_VERIFY', 'CHECK_SIGNATURE':'ED25519_VERIFY',
    'SEND':'P2P_SEND', 'TRANSMIT':'P2P_SEND',
    'RECEIVE':'P2P_RECV', 'LISTEN':'P2P_RECV',
    'RANDOM_NUMBER':'RANDOM', 'GENERATE_RANDOM':'RANDOM',
    'CURRENT_TIME':'TIME', 'NOW':'TIME', 'TIMESTAMP':'TIME',
    'EMBED':'EMBED_TEXT', 'MEANING_OF':'EMBED_TEXT', 'UNDERSTAND':'EMBED_TEXT',
    'SIMILARITY':'COSINE_SIM', 'HOW_SIMILAR':'COSINE_SIM', 'COMPARE_MEANING':'COSINE_SIM',
    'LOAD_AI_MODEL':'LOAD_MODEL', 'PREPARE_AI':'LOAD_MODEL',
    'STOP':'HALT', 'END':'HALT', 'FINISH':'HALT', 'DONE':'HALT',
    'DEBUG':'DEBUG_REG', 'SHOW_REGISTERS':'DEBUG_REG',
}

# Alias de registres pour QBM Human
REG_ALIASES = {
    'amount':'R0', 'value':'R0', 'result':'R0', 'score':'R0',
    'limit':'R1', 'threshold':'R1', 'max':'R1', 'cap':'R1',
    'counter':'R2', 'index':'R2', 'count':'R2', 'total':'R2',
    'source':'R3', 'sender':'R3',
    'destination':'R4', 'receiver':'R4',
    'parameter':'R5', 'input':'R5',
    'temp':'R6', 'tmp':'R6', 'scratch':'R6',
    'address':'R7', 'pointer':'R7',
    'budget':'R8', 'funds':'R8', 'money':'R8', 'watts':'R8',
    'signature':'R9', 'proof':'R9',
    'candidate':'R10', 'proposal':'R10', 'message':'R10',
    'reference':'R11', 'baseline':'R11', 'charter':'R11',
    'status':'R12', 'flag':'R12',
}

class QBM:
    def __init__(self):
        self.mem = bytearray(MEM_SIZE)
        self.regs = [0]*NUM_REGS
        self.flags = 0
        self.running = False
        self.regs[R_SP] = 0xFF00
        self.regs[R_PC] = 0
        self.p2p_inbox = []

    def load(self, bc, offset=0):
        for i, b in enumerate(bc):
            if offset+i < MEM_SIZE: self.mem[offset+i] = b
        self.regs[R_PC] = offset

    def rb(self):
        b = self.mem[self.regs[R_PC]]
        self.regs[R_PC] += 1
        return b

    def ro(self):
        m = self.rb()
        if m <= 0x0F: return self.regs[m]
        if m == MODE_IMM8: return self.rb()
        if m == MODE_IMM16:
            lo=self.rb(); hi=self.rb()
            return lo|(hi<<8)
        if m == MODE_IMM32:
            b0=self.rb(); b1=self.rb(); b2=self.rb(); b3=self.rb()
            return b0|(b1<<8)|(b2<<16)|(b3<<24)
        if 0x20 <= m <= 0x2F: return self.regs[m-0x20]
        if m == MODE_MEM_ABS:
            lo=self.rb(); hi=self.rb()
            return lo|(hi<<8)
        return 0

    def wr(self, reg, val):
        if reg < NUM_REGS: self.regs[reg] = val & 0xFFFFFFFF

    def step(self):
        if not self.running: return False
        op = self.rb()
        if op == OP_MOV:
            d = self.rb(); self.wr(d, self.ro())
        elif op == OP_ADD:
            d = self.rb(); r = self.regs[d] + self.ro()
            self.wr(d, r)
            self.flags = (self.flags & ~FLAG_C) | (FLAG_C if r > 0xFFFFFFFF else 0)
        elif op == OP_CMP:
            a=self.ro(); b=self.ro(); self.flags=0
            if a-b==0: self.flags|=FLAG_Z
            if a-b<0: self.flags|=FLAG_N
            if a<b: self.flags|=FLAG_C
        elif op == OP_JMP:
            c=self.rb(); t=self.ro(); j=False
            if c==0: j=True
            elif c==1 and (self.flags&FLAG_Z): j=True
            elif c==2 and not(self.flags&FLAG_Z): j=True
            elif c==3 and (self.flags&FLAG_C): j=True
            elif c==4 and not(self.flags&FLAG_C): j=True
            elif c==5 and (self.flags&FLAG_N): j=True
            if j: self.regs[R_PC]=t
        elif op == OP_CALL: self._nc(self.rb())
        elif op == OP_LOAD:
            d=self.rb(); a=self.ro()
            if 0<=a<MEM_SIZE:
                v=self.mem[a]|(self.mem[a+1]<<8)|(self.mem[a+2]<<16)|(self.mem[a+3]<<24)
                self.wr(d,v)
        elif op == OP_STOR:
            a=self.ro(); s=self.ro()
            if 0<=a<MEM_SIZE-3:
                self.mem[a]=s&0xFF; self.mem[a+1]=(s>>8)&0xFF
                self.mem[a+2]=(s>>16)&0xFF; self.mem[a+3]=(s>>24)&0xFF
        else: return False
        return self.running

    def _nc(self, rid):
        r=self.regs
        if rid==0x00: self.running=False
        elif rid==0x01:
            p,l=r[0],r[1]
            if l: sys.stdout.write(self.mem[p:p+l].decode('ascii',errors='replace'))
            else: sys.stdout.write(chr(r[0]&0xFF))
            sys.stdout.flush()
        elif rid==0x03:
            d=bytes(self.mem[r[0]:r[0]+r[1]])
            h=hashlib.sha256(d).digest()
            for i,b in enumerate(h): self.mem[r[2]+i]=b
        elif rid==0x04:
            k=bytes(self.mem[r[0]:r[0]+32])
            m=bytes(self.mem[r[1]:r[1]+r[2]])
            h=hashlib.sha256(k+m).digest()
            for i,b in enumerate(h+bytes(32)): self.mem[r[3]+i]=b
        elif rid==0x05: r[0]=1
        elif rid==0x06:
            dest=bytes(self.mem[r[0]:r[0]+32]).decode('ascii',errors='replace').strip('\x00')
            msg=bytes(self.mem[r[1]:r[1]+r[2]])
            self.p2p_inbox.append((dest,msg))
        elif rid==0x07:
            if self.p2p_inbox:
                _,msg=self.p2p_inbox.pop(0)
                for i,b in enumerate(msg[:r[1]]): self.mem[r[0]+i]=b
                r[0]=min(len(msg),r[1])
            else: r[0]=0
        elif rid==0x08:
            for i,b in enumerate(os.urandom(r[1])): self.mem[r[0]+i]=b
        elif rid==0x09: r[0]=int(time_module.time())
        elif rid==0x0E:
            n=["R0","R1","R2","R3","R4","R5","R6","R7","R8","R9","R10","R11","R12","LR","SP","PC"]
            for i in range(16): print(f"  {n[i]}: 0x{self.regs[i]:08X} ({self.regs[i]})")
        elif rid==0x0A:  # EMBED_TEXT — R0=ptr txt, R1=len, R2=ptr dest (1536 octets)
            try:
                txt = self.mem[r[0]:r[0]+r[1]].decode('utf-8', errors='replace')
                model = _get_st_model()
                emb = model.encode(txt, normalize_embeddings=True)
                emb_bytes = emb.astype('<f4').tobytes()
                for i, b in enumerate(emb_bytes):
                    if r[2]+i < MEM_SIZE:
                        self.mem[r[2]+i] = b
                r[0] = 1
            except Exception:
                r[0] = 0
        elif rid==0x0B:  # COSINE_SIM — R0=ptr emb1, R1=ptr emb2 → R0=score*10000
            try:
                import numpy as np
                b1 = bytes(self.mem[r[0]:r[0]+1536])
                b2 = bytes(self.mem[r[1]:r[1]+1536])
                e1 = np.frombuffer(b1, dtype='<f4')
                e2 = np.frombuffer(b2, dtype='<f4')
                sim = float(np.dot(e1, e2))
                r[0] = int(max(0.0, min(1.0, sim)) * 10000)
            except Exception:
                r[0] = 0
        elif rid==0x0C:  # LOAD_MODEL — prechargement explicite
            try:
                _get_st_model()
                r[0] = 1
            except Exception:
                r[0] = 0

    def run(self, mx=100000):
        self.running=True; s=0
        while self.running and s<mx:
            if not self.step(): break
            s+=1
        return s


class QBMAssembler:
    def __init__(self):
        self.labels={}; self.pending_refs=[]; self.output=bytearray()

    def po(self, token):
        token=token.strip().rstrip(',')
        # Resoudre alias de registre QBM Human
        if token.lower() in REG_ALIASES:
            token = REG_ALIASES[token.lower()]
        if token.isdigit() or (token.startswith('-') and token[1:].isdigit()):
            v=int(token)
            if -128<=v<=127: return [MODE_IMM8, v&0xFF]
            return [MODE_IMM16, v&0xFF, (v>>8)&0xFF]
        rm={'R0':0,'R1':1,'R2':2,'R3':3,'R4':4,'R5':5,'R6':6,'R7':7,
            'R8':8,'R9':9,'R10':10,'R11':11,'R12':12,'LR':13,'SP':14,'PC':15}
        if token.upper() in rm: return [rm[token.upper()]]
        if token.startswith('[') and token.endswith(']'):
            r=token[1:-1].upper()
            if r in rm: return [MODE_MEM_REG+rm[r]]
        if token.startswith('@'):
            self.pending_refs.append((len(self.output)+1, token[1:]))
            return [MODE_IMM16, 0, 0]
        if token.startswith('#'):
            vs=token[1:]
            v=int(vs,16) if vs.startswith('0x') else int(vs)
            if 0<=v<=255: return [MODE_IMM8, v]
            if 0<=v<=65535: return [MODE_IMM16, v&0xFF, (v>>8)&0xFF]
            return [MODE_IMM32, v&0xFF, (v>>8)&0xFF, (v>>16)&0xFF, (v>>24)&0xFF]
        if token.startswith('0x'):
            a=int(token,16)
            return [MODE_IMM16, a&0xFF, (a>>8)&0xFF]
        if token and token[0].isalpha():
            self.pending_refs.append((len(self.output)+1, token))
            return [MODE_IMM16, 0, 0]
        return []

    def al(self, line):
        if ';' in line: line=line.split(';')[0]
        line=line.strip()
        if not line or line.startswith('#'): return
        if line.endswith(':'):
            self.labels[line[:-1].strip()]=len(self.output); return
        if line.startswith('.ascii'):
            self.output.extend(line.split('.ascii',1)[1].strip().strip('"').encode('ascii')); return
        if line.startswith('.byte'):
            for v in line.split('.byte',1)[1].strip().split(','):
                v=v.strip()
                self.output.append(int(v,16) if v.startswith('0x') else int(v))
            return
        if line.startswith('.word'):
            for v in line.split('.word',1)[1].strip().split(','):
                v=v.strip()
                val=int(v,16) if v.startswith('0x') else int(v)
                self.output.extend([val&0xFF,(val>>8)&0xFF,(val>>16)&0xFF,(val>>24)&0xFF])
            return
        p=line.split(None,1)
        mn=p[0].upper(); ops=p[1] if len(p)>1 else ''
        # Resoudre alias mnemonique QBM Human
        if mn in MNEMONIC_ALIASES:
            resolved = MNEMONIC_ALIASES[mn]
            if ' ' in resolved:
                # Alias composite (ex: 'JMP 0,' → JMP + cond)
                parts = resolved.split(' ',1)
                mn = parts[0].upper()
                ops = parts[1] + (' ' + ops if ops else '')
            else:
                mn = resolved.upper()
        if mn=='MOV':
            self.output.append(OP_MOV); o=ops.split(',',1)
            self.output.extend(self.po(o[0].strip()))
            self.output.extend(self.po(o[1].strip()))
        elif mn=='ADD':
            self.output.append(OP_ADD); o=ops.split(',',1)
            self.output.extend(self.po(o[0].strip()))
            self.output.extend(self.po(o[1].strip()))
        elif mn=='CMP':
            self.output.append(OP_CMP); o=ops.split(',',1)
            self.output.extend(self.po(o[0].strip()))
            self.output.extend(self.po(o[1].strip()))
        elif mn=='JMP':
            self.output.append(OP_JMP); o=ops.split(',',1)
            self.output.append(int(o[0].strip()))
            self.output.extend(self.po(o[1].strip()))
        elif mn=='CALL':
            self.output.append(OP_CALL); tok=ops.strip()
            if tok in NATIVE_NAMES.values():
                for k,v in NATIVE_NAMES.items():
                    if v==tok: self.output.append(k); break
            else:
                try: self.output.append(int(tok))
                except: self.output.append(0)
        elif mn=='LOAD':
            self.output.append(OP_LOAD); o=ops.split(',',1)
            self.output.extend(self.po(o[0].strip()))
            self.output.extend(self.po(o[1].strip()))
        elif mn=='STOR':
            self.output.append(OP_STOR); o=ops.split(',',1)
            self.output.extend(self.po(o[0].strip()))
            self.output.extend(self.po(o[1].strip()))

    def assemble(self, source):
        self.labels={}; self.pending_refs=[]; self.output=bytearray()
        for line in source.split('\n'): self.al(line)
        for off, label in self.pending_refs:
            if label in self.labels:
                a=self.labels[label]
                self.output[off]=a&0xFF; self.output[off+1]=(a>>8)&0xFF
        return bytes(self.output)


def run_demos():
    sys.stdout.reconfigure(encoding='utf-8')
    a=QBMAssembler()

    print("="*50)
    print("QBM DEMO #1 -- Hello, Silicium")
    print("="*50)
    vm=QBM()
    vm.load(a.assemble("""
        MOV R0, @msg
        MOV R1, #16
        CALL CONSOLE_OUT
        CALL HALT
    msg:
        .ascii "Hello, Silicium!"
    """))
    vm.run()

    print("\n"+"="*50)
    print("QBM DEMO #2 -- Addition baremetal")
    print("="*50)
    vm=QBM()
    vm.load(a.assemble("""
        MOV R0, #42
        MOV R1, #58
        ADD R0, R1
        CALL DEBUG_REG
        CALL HALT
    """))
    vm.run()
    print(f"\n[QBM] R0 = {vm.regs[0]} (42 + 58)")

    print("\n"+"="*50)
    print("QBM DEMO #3 -- Transfert P2P simule")
    print("="*50)
    vm=QBM()
    vm.load(a.assemble("""
        MOV R0, @dest
        MOV R1, @msg
        MOV R2, #5
        CALL P2P_SEND
        MOV R0, @sent
        MOV R1, #19
        CALL CONSOLE_OUT
        CALL HALT
    dest:
        .ascii "maman"
    msg:
        .ascii "50EUR"
    sent:
        .ascii "Transaction envoyee"
    """))
    vm.run()
    print(f"\n[QBM] Messages P2P: {len(vm.p2p_inbox)}")
    for dest,msg in vm.p2p_inbox:
        print(f"  -> {dest}: {msg}")

    print("\n"+"="*50)
    print("QBM DEMO #4 -- Gouvernance par similarite semantique")
    print("(MiniLM-L6-v2 embarque, ~80 Mo au premier appel)")
    print("="*50)
    vm=QBM()
    vm.load(a.assemble("""
        ; Precharger le modele (80 Mo, une seule fois)
        CALL LOAD_MODEL

        ; Embed le message candidat
        MOV R0, @candidate
        MOV R1, @cand_len
        MOV R2, @emb_candidate
        CALL EMBED_TEXT

        ; Embed la reference "bienveillante"
        MOV R0, @reference
        MOV R1, @ref_len
        MOV R2, @emb_reference
        CALL EMBED_TEXT

        ; Cosine similarity entre les deux
        MOV R0, @emb_candidate
        MOV R1, @emb_reference
        CALL COSINE_SIM
        ; R0 = score * 10000

        ; Seuil de bienveillance : 7000/10000
        MOV R1, #7000
        CMP R0, R1
        JMP 3, rejeter

        ; Approuve
        MOV R0, @ok
        MOV R1, #10
        CALL CONSOLE_OUT
        CALL HALT

    rejeter:
        MOV R0, @ko
        MOV R1, #7
        CALL CONSOLE_OUT
        CALL HALT

    candidate:
        .ascii "Tu es un champion, continue comme ca !"
    reference:
        .ascii "Tu es formidable et je crois en toi."
    ok:
        .ascii "APPROUVE"
    ko:
        .ascii "REJETE"
    """))
    vm.run()
    print(f"\n[QBM] Score de similarite: {vm.regs[0]}/10000")

    print("\n"+"="*50)
    print("QBM -- Fin des demos. Le silicium a parle.")
    print("="*50)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv)<2:
        print("QBM -- Quantum BareMetal VM v1.1")
        print("  Instructions: MOV ADD CMP JMP CALL LOAD STOR")
        print("  Appels natifs: HALT CONSOLE_OUT HASH_SHA256 ED25519_SIGN ED25519_VERIFY")
        print("                 P2P_SEND P2P_RECV RANDOM TIME")
        print("                 EMBED_TEXT COSINE_SIM LOAD_MODEL  <-- semantique")
        print("Usage: python qbm.py --demo")
        print("       python qbm.py <fichier.qbm>")
        sys.exit(0)
    if sys.argv[1]=='--demo':
        run_demos(); return
    a=QBMAssembler()
    with open(sys.argv[1], encoding='utf-8') as f:
        bc=a.assemble(f.read())
    print(f"[QBM] Assemble: {len(bc)} octets")
    vm=QBM(); vm.load(bc); s=vm.run()
    print(f"[QBM] Execution terminee en {s} cycles")


if __name__=='__main__':
    main()
