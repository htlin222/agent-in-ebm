<!-- 附錄 A–D。術語出處與正文一致、皆經 Crossref/PubMed 查證；自由度地圖分級對應 figures/fig03，為定性判斷非量化測量 -->

# 附錄

## 附錄 A · 術語對照表

方法學名詞第一次在正文出現時都先用白話解釋過；這裡按出現順序整理，供回查。臨床名詞（臨床試驗、隨機分派、統合分析、療效）不列入。

| 中文 | 英文 | 一句話定義 | 出處 |
|---|---|---|---|
| 系統性回顧 | systematic review | 先把納入規則寫死、再照規則收論文的文獻回顧，不是「讀很多論文」 | Cochrane Handbook, 2019 |
| 預先註冊 | preregistration | 在動手前把研究規則公開登記，讓人不能等看到結果再改規則 | Nosek 2018 |
| PROSPERO | — | 系統性回顧的公開登記處 | — |
| 雙人獨立篩選 | dual independent screening | 兩個人各自獨立判斷收錄、再對答案，是文獻篩選的黃金標準 | Wang 2020 |
| 選擇性報告 | selective reporting | 一項研究量了多個指標、只報好看的那個；即「挑好結果」 | RoB 2 domain 5, Sterne 2019 |
| kappa | Cohen's kappa | 兩個判斷者一致的程度，扣掉瞎猜也會碰巧一致的部分（1 全一致，0 等於丟銅板） | — |
| 資料萃取 | data extraction | 把散在各篇論文的數字抄進同一張表，好放在一起算 | — |
| IMRaD | — | 前言／方法／結果／討論的論文格式，是編輯慣例不是自然律 | Sollaci 2004 |
| PRISMA 2020 | — | 系統性回顧的報告規範（管你有沒有說清楚，不管你做得對不對） | Page 2021 |
| 研究者自由度 | researcher degrees of freedom | 分析途中「可以晚點再決定」的選擇空間 | Simmons 2011 |
| 分岔路徑花園 | garden of forking paths | 同一問題走不同岔路得到不同結論、每條單看都合理 | Gelman & Loken 2014 |
| GRADE | — | 替證據可信度分級的方法；它自承是「結構化的判斷」 | Guyatt 2011 |
| 協定的可執行化 | protocol-as-code | 把研究規則寫成機器讀得懂、可版控的設定檔，而非一段散文 | — |
| 定址性 | addressability | 能穩穩指著「這個結論在哪一個版本／狀態下成立」的能力 | Elliott 2014 |
| 版本庫 | version control / repository | 會把每次改動都留檔、可回溯查閱的檔案倉庫 | — |
| 迴圈終止條件的內生／外生 | endogenous / exogenous termination | 讓自動化迴圈停下來的條件，是長在模型自己之內、還是模型之外的現實 | — |
| 自我偏好偏誤 | self-preference bias | 語言模型認得出並偏好自己的產出，使自評分數失真 | Panickssery 2024 |
| 流程可重現 vs 結果可重現 | process vs result reproducibility | 前者＝每個決定與環境都能取回重跑；後者＝重跑得到同樣輸出 | Peng 2011 |
| 型一錯誤 | type I error | 把其實不存在的效果誤判為存在（偽陽性） | Simmonds 2017 |
| 非劣性 | non-inferiority | 新方法「不比舊方法差」的統計檢定門檻 | Arno 2022 |
| 真實性疑慮 | trustworthiness / integrity concern | 試驗可能造假、數字不可能、病人根本沒收——偏誤工具抓不到的一層 | Wilkinson 2025 (INSPECT-SR) |
| 一等公民資料 | first-class data | 把「這次放寬了哪些關卡」寫成只能追加、不能改寫的結構化紀錄，而非敘述裡一句話 | — |
| 對抗式驗證 | adversarial verification | 用多個獨立角度、預設「不成立」去審同一個結論，過半才算數 | — |

## 附錄 B · 自由度地圖完整版

對應圖 3。各階段依「現行規範是否要求事前指定」定位，分為**自動化成熟度**與**偏誤棲居度**兩軸；此處為定性判斷，非量化測量。由最機械（上）到最需判斷（下）排列。

| 階段 | 自由度 | 自動化成熟度 | 偏誤棲居度 |
|---|---|---|---|
| 去重 | 極低 | 極高 | 極低 |
| DOI／引用解析 | 極低 | 極高 | 極低 |
| 統計合併（計算） | 低 | 高 | 低 |
| 檢索執行 | 低 | 高 | 低—中 |
| 流程圖計數 | 低 | 高 | 低 |
| 標題摘要初篩 | 中 | 中—高 | 中 |
| 資料萃取 | 中 | 中 | 中 |
| 全文合格判定 | 中—高 | 中—低 | 中—高 |
| 偏誤風險評估 | 高 | 低 | 高 |
| GRADE 間接性 | 高 | 極低 | 極高 |
| 選擇性報告判斷 | 極高 | 極低 | 極高（Gates 2018：κ=0.02） |

**讀法**：自動化這些年攻下的是上半（自由度最低的幾格），偏誤住在下半（腦力那一端）。兩軸恰好反向交叉，交叉點落在資料萃取一帶。

## 附錄 C · 論證結構

本章的完整論證已形式化並公開，見 `argument/chapter-thesis.argdown`（38 個論證、30 條關係；17 攻擊、13 支持，lint 通過，可渲染成 SVG／DOT／JSON）。任何一步都可以被單獨指名反駁——**這句話本身就是本章主張的示範，不要求讀者看懂論證圖。**

主要節點：被駁斥的原始命題〔人少即德性〕／被採納的主命題〔偏誤遷移論〕〔未受約束的自由度是偏誤來源〕／規範性結論〔揭露單位位移〕〔迴圈可信度判準〕／形式化與多模型共識／自證案例／新穎性宣稱〔兩個問題不同〕〔適用範圍限縮〕。

## 附錄 D · 圖表原始碼

所有圖由程式碼產生、與正文一起版控，可逐張重建。

| 圖 | 出現於 | 原始碼 | 重建指令 |
|---|---|---|---|
| 1 造假是怎麼發生的 | §0 | `figures/fig01-fabrication.dot` | `dot -Tpng fig01-fabrication.dot -o fig01.png` |
| 2 IMRaD 的那道縫 | §2 | `figures/fig02-imrad-gap.dot` | `dot -Tpng fig02-imrad-gap.dot -o fig02-imrad-gap.png` |
| 3 自由度地圖 | §3 | `figures/fig03_freedom_map.py` | `uv run --with matplotlib python3 fig03_freedom_map.py` |
| 4 四種迴圈 | §4 | `figures/fig04-loops.dot` | `dot -Tpng fig04-loops.dot -o fig04-loops.png` |
| 5 表演性的獨立 | §5 | `figures/fig05-performative-independence.puml` | `plantuml -tpng fig05-performative-independence.puml` |
