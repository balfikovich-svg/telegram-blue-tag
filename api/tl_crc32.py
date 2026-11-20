import zlib,re,sys
lines=[l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith('//') and not l.startswith('---')]
out=[]
for l in lines:
    name,rest=l.split(' ',1)
    base=re.sub(r'#[0-9a-f]+$','',name)
    s=(base+' '+rest).rstrip(';').strip()
    s=re.sub(r'\s+',' ',s)
    cid=format(zlib.crc32(s.encode())&0xffffffff,'08x')
    out.append(f"{base}#{cid} {rest}")
print('\n'.join(out))
