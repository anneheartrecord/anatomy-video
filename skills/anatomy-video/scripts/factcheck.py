#!/usr/bin/env python3
"""Fact-check table for a video script: extract the claims, then gate the render on them.

  factcheck.py extract audio/narration.txt source/factcheck.md     # list every sentence that states a fact
  factcheck.py gate source/factcheck.md --narration audio/narration.txt --page index.html

extract  picks sentences with numbers, prices, dates, quotas or factual wording (free, launched, official ...)
         and writes a Markdown table to fill in. Re-running keeps rows you already filled and adds new ones.
gate     exits 1 (do not render) when a row has no status, is still 未核实, or is 已核 / 二手 without a URL;
         warns about claims in the narration that are missing from the table, rows whose sentence was
         removed from the script, and numbers drawn on screen (string literals in the page) that appear
         neither in the narration nor in the table, e.g. an illustrative "第 7 轮" that should say 示意.

Status values:
  已核    you opened the primary source (official page, docs, announcement) and it matches
  二手    only media or user reports; the script must say so (有用户反馈 / 报道称)
  计算    derived from verified numbers; write the formula in 备注 (e.g. 10000 ÷ 21.75 ÷ 8 ≈ 57)
  示意    an illustrative example; it must be labelled 示意 on screen
  观点    the author's own judgement; no source needed
  删除    removed from the script
  未核实  not checked yet; blocks the render
"""
import argparse, os, re, sys

STATUSES = ['已核', '二手', '计算', '示意', '观点', '删除', '未核实']
CLAIM = re.compile(r'\d|[零一二两三四五六七八九十百千万亿]+(?:元|块|倍|个月|年|天|小时|分钟|次|轮|人|张|个|成|折|%)|'
                   r'¥|\$|%|免费|收费|价格|会员|积分|额度|上线|发布|推出|截至|官方|数据|报告|研究|调查|统计|据|第一|最')
HEAD = ['#', '稿中说法', '出处（URL）', '来源日期', '状态', '备注']


def sentences(path):
    text = open(path, encoding='utf-8').read().replace('\n', '')
    return [s.strip() for s in re.findall(r'[^。！？；]+[。！？；]?', text) if s.strip()]


def read_table(path):
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding='utf-8'):
        if not line.startswith('|') or line.startswith('|---') or line.startswith('| #'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) >= 6:
            rows.append(dict(zip(HEAD, cells[:6])))
    return rows


def write_table(path, rows):
    out = ['# 事实核对表', '',
           '状态只能填：' + ' / '.join(STATUSES) + '。规则见 references/fact-check.md。', '',
           '| ' + ' | '.join(HEAD) + ' |', '|' + '---|' * len(HEAD)]
    for i, r in enumerate(rows, 1):
        r['#'] = str(i)
        out.append('| ' + ' | '.join(r.get(h, '').replace('|', '／') for h in HEAD) + ' |')
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    open(path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')


def extract(a):
    old = {r['稿中说法']: r for r in read_table(a.table)}
    claims = [s for s in sentences(a.narration) if CLAIM.search(s)]
    rows = [old.get(s, {'稿中说法': s, '出处（URL）': '', '来源日期': '', '状态': '', '备注': ''}) for s in claims]
    rows += [r for s, r in old.items() if s not in claims and r['状态'] == '删除']
    write_table(a.table, rows)
    print(f'{a.table}: {len(rows)} claims ({sum(1 for s in claims if s not in old)} new). Fill in 出处 / 来源日期 / 状态.')


def gate(a):
    rows = read_table(a.table)
    errors, warnings = [], []
    for r in rows:
        st, url, claim = r['状态'], r['出处（URL）'], r['稿中说法'][:40]
        if st not in STATUSES:
            errors.append(f'#{r["#"]} no valid status: {claim}')
        elif st == '未核实':
            errors.append(f'#{r["#"]} still 未核实: {claim}')
        elif st in ('已核', '二手') and not url.startswith('http'):
            errors.append(f'#{r["#"]} {st} but no URL: {claim}')
        elif st == '计算' and not r['备注']:
            errors.append(f'#{r["#"]} 计算 but no formula in 备注: {claim}')
    if a.narration:
        sents = sentences(a.narration)
        listed = {r['稿中说法'] for r in rows}
        for s in sents:
            if CLAIM.search(s) and s not in listed:
                warnings.append(f'claim not in table (run extract again): {s[:40]}')
        for r in rows:
            if r['状态'] != '删除' and r['稿中说法'] not in sents:
                warnings.append(f'#{r["#"]} sentence no longer in the script: {r["稿中说法"][:40]}')
    if a.page:
        page = open(a.page, encoding='utf-8').read()
        known = (open(a.narration, encoding='utf-8').read() if a.narration else '') + ' '.join(' '.join(r.values()) for r in rows)
        strings = re.findall(r"'([^'\n]*\d[^'\n]*)'|\"([^\"\n]*\d[^\"\n]*)\"", page)
        seen = set()
        for s1, s2 in strings:
            s = s1 or s2
            if not re.search(r'[\u4e00-\u9fff¥$%×÷≈]', s) or re.search(r'[#(){};=<>]|px|rgba?|\.(js|css|png)', s):
                continue                                    # on-screen text has CJK / currency / %; skip code, colors, sizes
            for num in re.findall(r'\d+(?:\.\d+)?', s):
                if num not in known and (s, num) not in seen:
                    seen.add((s, num)); warnings.append(f'on-screen number {num} in "{s}" is not in the script or table (示意?)')
    for w in warnings:
        print('WARN ', w)
    for e in errors:
        print('BLOCK', e)
    ok = not errors
    print(f'{len(rows)} claims, {len(errors)} blocking, {len(warnings)} warnings -> {"OK to render" if ok else "fix before rendering"}')
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('extract'); e.add_argument('narration'); e.add_argument('table')
    g = sub.add_parser('gate'); g.add_argument('table'); g.add_argument('--narration'); g.add_argument('--page')
    a = ap.parse_args()
    (extract if a.cmd == 'extract' else gate)(a)


if __name__ == '__main__':
    main()
