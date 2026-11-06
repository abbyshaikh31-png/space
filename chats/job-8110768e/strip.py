p='ai-transformer-guide.html'
s=open(p).read()
tail='</main>\n</div>\n</body>\n</html>\n'
if tail in s:
    s=s.replace(tail,'')
    open(p,'w').write(s)
    print('stripped ok', len(s))
else:
    print('tail not found')
    print(repr(s[-120:]))
]<]minimax[>[