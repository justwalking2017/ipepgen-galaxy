import hashlib, sys
from Bio import SeqIO

seen = set()
with open(sys.argv[1], "w", encoding="utf-8") as out:
    for path in sys.argv[2:]:
        for record in SeqIO.parse(path, "fasta"):
            seq = str(record.seq).upper().replace("*", "")
            digest = hashlib.sha256(seq.encode()).digest()
            if seq and digest not in seen:
                seen.add(digest); out.write(f">{record.description}\n{seq}\n")

