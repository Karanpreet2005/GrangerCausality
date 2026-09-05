"""Dependency-free PDF text extractor.

Built for this reproduction because the machine has no poppler/pdftotext and no
pypdf/PyMuPDF. Parses PDF objects directly, inflates FlateDecode streams, and maps
character codes to Unicode via /ToUnicode CMaps or /Encoding /Differences glyph names.

Usage:  python tools/pdf_extract.py FILE.pdf [first_page] [last_page]
"""
import re, zlib, sys
FN = sys.argv[1]
data=open(FN,'rb').read()

objs={}
for m in re.finditer(rb'(?<![0-9])(\d+)\s+(\d+)\s+obj\b', data):
    num=int(m.group(1)); start=m.end(); e=data.find(b'endobj', start)
    objs[num]=data[start:e]

def deref(tok):
    m=re.match(rb'\s*(\d+)\s+\d+\s+R', tok)
    return objs.get(int(m.group(1)), b'') if m else tok

def getstream(body):
    m=re.search(rb'stream\r?\n', body)
    if not m: return None
    raw=body[m.end():]; e=raw.rfind(b'endstream'); raw=raw[:e]
    if b'/FlateDecode' in body[:m.start()]:
        try: return zlib.decompress(raw)
        except Exception:
            try: return zlib.decompressobj().decompress(raw)
            except Exception: return None
    return raw

# --- glyph name -> unicode ---
NAMES={'space':' ','exclam':'!','quotedbl':'"','numbersign':'#','dollar':'$','percent':'%',
'ampersand':'&','quoteright':"'",'quotesingle':"'",'parenleft':'(','parenright':')','asterisk':'*',
'plus':'+','comma':',','hyphen':'-','period':'.','slash':'/','colon':':','semicolon':';',
'less':'<','equal':'=','greater':'>','question':'?','at':'@','bracketleft':'[','backslash':'\\',
'bracketright':']','asciicircum':'^','underscore':'_','quoteleft':'`','braceleft':'{','bar':'|',
'braceright':'}','asciitilde':'~','endash':'–','emdash':'—','quotedblleft':'“',
'quotedblright':'”','quotedblbase':'„','bullet':'•','dagger':'†',
'copyright':'©','registered':'®','degree':'°','minus':'−','endash1':'-',
'fi':'fi','fl':'fl','f_i':'fi','f_l':'fl','f_f':'ff','f_f_i':'ffi','f_f_l':'ffl','ff':'ff','ffi':'ffi','ffl':'ffl',
'zero':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9',
'alpha':'α','beta':'β','gamma':'γ','delta':'δ','epsilon':'ε','zeta':'ζ',
'eta':'η','theta':'θ','iota':'ι','kappa':'κ','lambda':'λ','mu':'μ',
'nu':'ν','xi':'ξ','pi':'π','rho':'ρ','sigma':'σ','tau':'τ',
'upsilon':'υ','phi':'φ','chi':'χ','psi':'ψ','omega':'ω',
'Gamma':'Γ','Delta':'Δ','Theta':'Θ','Lambda':'Λ','Xi':'Ξ','Pi':'Π',
'Sigma':'Σ','Upsilon':'Υ','Phi':'Φ','Psi':'Ψ','Omega':'Ω',
'infinity':'∞','summation':'∑','product':'∏','integral':'∫','radical':'√',
'element':'∈','arrowright':'→','arrowleft':'←','lessequal':'≤','greaterequal':'≥',
'notequal':'≠','approxequal':'≈','similar':'∼','multiply':'×','divide':'÷',
'prime':'′','partialdiff':'∂','logicalnot':'¬','universal':'∀','existential':'∃',
'circumflex':'^','tilde':'~','acute':'´','grave':'`','dieresis':'¨','cedilla':'¸',
'ring':'˚','breve':'˘','macron':'¯','dotaccent':'˙','caron':'ˇ','hungarumlaut':'˝',
'ellipsis':'…','perthousand':'‰','florin':'ƒ','germandbls':'ß','ae':'æ','oe':'œ',
'oslash':'ø','AE':'Æ','OE':'Œ','Oslash':'Ø','dotlessi':'ı','sterling':'£',
'section':'§','paragraph':'¶','plusminus':'±','union':'∪','intersection':'∩',
'angbracketleft':'⟨','angbracketright':'⟩','bardbl':'‖','braceleftbig':'{','bracerightbig':'}',
'parenleftbig':'(','parenrightbig':')','parenleftBig':'(','parenrightBig':')',
'parenleftbigg':'(','parenrightbigg':')','bracketleftbig':'[','bracketrightbig':']',
'summationdisplay':'∑','integraldisplay':'∫','summationtext':'∑',
'arrowdblright':'⇒','arrowdbl':'⇒','propersubset':'⊂','reflexsubset':'⊆',
'emptyset':'∅','turnstileleft':'⊢','perpendicular':'⊥','bar1':'|','asteriskmath':'*',
'periodcentered':'·','dotmath':'⋅','circlemultiply':'⊗','circleplus':'⊕',
'Phi1':'Φ','negationslash':'\u0338','notarrowright':'↛','theta1':'ϑ','phi1':'ϕ','epsilon1':'ϵ','rho1':'ϱ','sigma1':'ς',
'hatwide':'^','tildewide':'~','vector':'⃗','arrowhookleft':'↩','bracehtipdownleft':'','bracehtipdownright':'',
'bracehtipupleft':'','bracehtipupright':'','braceex':'','bracelefttp':'{','braceleftbt':'{','braceleftmid':'{',
'parenlefttp':'(','parenleftbt':'(','parenrighttp':')','parenrightbt':')','parenleftex':'','parenrightex':'',
'radicalbig':'√','radicalBig':'√','bardblbig':'‖','vextendsingle':'|','vextenddouble':'‖',
}
def gname2uni(n):
    if n in NAMES: return NAMES[n]
    if len(n)==1: return n
    m=re.fullmatch(r'uni([0-9A-Fa-f]{4})', n)
    if m: return chr(int(m.group(1),16))
    m=re.fullmatch(r'u([0-9A-Fa-f]{4,6})', n)
    if m: return chr(int(m.group(1),16))
    if re.fullmatch(r'[A-Za-z]', n[0]) and n[1:].isdigit(): return n[0]
    return ''

STD=[None]*256
for i,ch in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'): STD[65+i]=ch
for i,ch in enumerate('abcdefghijklmnopqrstuvwxyz'): STD[97+i]=ch
for i in range(48,58): STD[i]=chr(i)
for i in range(32,127):
    if STD[i] is None: STD[i]=chr(i)

def parse_tounicode(s):
    mp={}
    for blk in re.findall(rb'beginbfchar(.*?)endbfchar', s, re.S):
        for a,b in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            try: mp[int(a,16)]=bytes.fromhex(b.decode()).decode('utf-16-be','replace')
            except Exception: pass
    for blk in re.findall(rb'beginbfrange(.*?)endbfrange', s, re.S):
        for m in re.finditer(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(?:<([0-9A-Fa-f]+)>|\[(.*?)\])', blk, re.S):
            lo=int(m.group(1),16); hi=int(m.group(2),16)
            if m.group(3):
                base=bytes.fromhex(m.group(3).decode()).decode('utf-16-be','replace')
                for i in range(lo,min(hi,lo+65535)+1):
                    mp[i]=chr(ord(base[0])+i-lo)+base[1:] if base else ''
            else:
                for i,it in enumerate(re.findall(rb'<([0-9A-Fa-f]+)>', m.group(4))):
                    mp[lo+i]=bytes.fromhex(it.decode()).decode('utf-16-be','replace')
    return mp

fc={}
def font_map(ref):
    if ref in fc: return fc[ref]
    body=objs.get(ref,b'')
    two = b'/Type0' in body
    cmap=None
    m=re.search(rb'/ToUnicode\s+(\d+)\s+\d+\s+R', body)
    if m:
        s=getstream(objs.get(int(m.group(1)),b''))
        if s: cmap=parse_tounicode(s)
    enc=None
    if cmap is None and not two:
        em=re.search(rb'/Encoding\s*(\d+\s+\d+\s+R|<<)', body)
        encbody=b''
        if em:
            if em.group(1)==b'<<':
                depth=0; i=em.start(1)
                while i<len(body):
                    if body[i:i+2]==b'<<': depth+=1; i+=2
                    elif body[i:i+2]==b'>>':
                        depth-=1; i+=2
                        if depth==0: break
                    else: i+=1
                encbody=body[em.start(1):i]
            else:
                encbody=deref(em.group(1))
        enc=list(STD)
        dm=re.search(rb'/Differences\s*\[(.*?)\]', encbody, re.S)
        if dm:
            code=0
            for tok in re.finditer(rb'(\d+)|/([A-Za-z0-9_.]+)', dm.group(1)):
                if tok.group(1): code=int(tok.group(1))
                else:
                    if code<256: enc[code]=gname2uni(tok.group(2).decode('latin-1'))
                    code+=1
    fc[ref]=(cmap, enc, two)
    return fc[ref]

pages=[]
for num,body in objs.items():
    if re.search(rb'/Type\s*/Page[^s]', body): pages.append((num,body))
pages.sort(key=lambda t:t[0])

def resolve_fonts(body):
    fonts={}
    m=re.search(rb'/Resources\s*(\d+\s+\d+\s+R|<<)', body)
    rbody=body
    if m and m.group(1)!=b'<<': rbody=deref(m.group(1))
    fm=re.search(rb'/Font\s*<<(.*?)>>', rbody, re.S)
    if not fm:
        fm2=re.search(rb'/Font\s+(\d+)\s+\d+\s+R', rbody)
        if fm2:
            fm=re.search(rb'<<(.*?)>>', objs.get(int(fm2.group(1)),b''), re.S)
    if fm:
        for name,ref in re.findall(rb'/([A-Za-z0-9_.+-]+)\s+(\d+)\s+\d+\s+R', fm.group(1)):
            fonts[name]=int(ref)
    return fonts

def unescape(s):
    out=bytearray(); i=0
    mp={0x6e:10,0x72:13,0x74:9,0x62:8,0x66:12,0x28:40,0x29:41,0x5c:92}
    while i<len(s):
        c=s[i]
        if c==0x5c and i+1<len(s):
            n=s[i+1]
            if n in mp: out.append(mp[n]); i+=2
            elif 0x30<=n<=0x37:
                j=i+1; oc=''
                while j<len(s) and len(oc)<3 and 0x30<=s[j]<=0x37: oc+=chr(s[j]); j+=1
                out.append(int(oc,8)&0xFF); i=j
            elif n==10: i+=2
            else: out.append(n); i+=2
        else: out.append(c); i+=1
    return bytes(out)

def decode(raw, f):
    cmap, enc, two = f
    o=[]
    if two:
        for i in range(0,len(raw)-1,2):
            c=(raw[i]<<8)|raw[i+1]
            o.append(cmap.get(c,'') if cmap else (chr(c) if 32<=c<0x2fff else ''))
    else:
        for b in raw:
            if cmap and b in cmap: o.append(cmap[b])
            elif enc is not None: o.append(enc[b] or '')
            else: o.append(chr(b))
    return ''.join(o)

lo = int(sys.argv[2]) if len(sys.argv) > 2 else 1
hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
for idx,(num,body) in enumerate(pages,1):
    if idx<lo or idx>hi: continue
    fonts=resolve_fonts(body)
    content=b''
    cm=re.search(rb'/Contents\s+(\d+)\s+\d+\s+R', body)
    if cm: content=getstream(objs.get(int(cm.group(1)),b'')) or b''
    else:
        cm2=re.search(rb'/Contents\s*\[(.*?)\]', body, re.S)
        if cm2:
            for r in re.findall(rb'(\d+)\s+\d+\s+R', cm2.group(1)):
                content += (getstream(objs.get(int(r),b'')) or b'')
    print(f"\n=============== PAGE {idx} ===============")
    cur=(None,STD,False); buf=[]
    pat=rb'/([A-Za-z0-9_.+-]+)\s+[\d.]+\s+Tf|\[((?:[^\[\]\\]|\\.)*)\]\s*TJ|(\((?:\\.|[^\\()])*\))\s*Tj|(T\*)|(-?[\d.]+)\s+(-?[\d.]+)\s+(Td|TD)'
    for m in re.finditer(pat, content, re.S):
        if m.group(1):
            r=fonts.get(m.group(1)); cur=font_map(r) if r else (None,STD,False)
        elif m.group(2) is not None:
            s=''
            for sm in re.finditer(rb'\((?:\\.|[^\\()])*\)|(-?[\d.]+)', m.group(2), re.S):
                if sm.group(1):
                    try:
                        if float(sm.group(1))<-100: s+=' '
                    except Exception: pass
                else: s+=decode(unescape(sm.group(0)[1:-1]), cur)
            buf.append(s)
        elif m.group(3): buf.append(decode(unescape(m.group(3)[1:-1]), cur))
        elif m.group(4): buf.append('\n')
        else:
            try:
                if float(m.group(6))!=0: buf.append('\n')
                else: buf.append(' ')
            except Exception: buf.append('\n')
    t=''.join(buf)
    t=re.sub(r'[ \t]+',' ',t)
    t=re.sub(r'\n{3,}','\n\n',t)
    print(t)
