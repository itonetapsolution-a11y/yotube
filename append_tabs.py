extra = open('ig_pt_tabs.py', encoding='utf-8').read()
with open('app.py', 'a', encoding='utf-8') as f:
    f.write(extra)
print('Done - tabs appended to app.py!')
