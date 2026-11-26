# 空母.net（xn--3owz62a.net）作業ルール

GitHub Pages の静的サイト。tools/build.py が tools/content/*.html から生成（お祭り.netの仕組みを流用）。
- tools/content/<dir>__<slug>.html → /<dir>/<slug>/（dir：us 米海軍の空母、cn 中国の空母。今後 world 各国 など）。slug は英小文字と数字のみ
- 1行目 title（末尾「｜空母.net」）、2行目 description、本文は h1・p.updated・導入・h2…、最後に section.sources
- data/navy_news.json：tools/fetch_navy.py が navy.mil 公式RSSから空母関連の見出し・日付・リンクを6時間ごとに取得（Actions: navy.yml）。トップと /us/ に自動表示
- 事実は米海軍・各艦隊・防衛省・外務省・各国海軍の公式発表だけ。報道・Wikipedia・ブログは不可（公式発表を探す手がかりにだけ使う）
- 空母の現在位置を推測で書かない。公式に発表された寄港・展開・改修のみ、日付つき
- 中立。特定の国・立場を支持・批判しない
- 1ページ本文3,000文字以上（トップ・規約を除く）
