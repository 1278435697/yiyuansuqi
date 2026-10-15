# -*- coding: utf-8 -*-
"""面料工艺素材（fabrics.json 导入版）：分步制作流程 / 工艺示意图 / 史料依据"""

CRAFT_MAP = {
    "葛布": {
        "steps": [{"num": 1, "num_cn": "①", "label": "采割葛藤", "title": "采葛", "desc": "入山谷采割葛藤，取其韧皮"}, {"num": 2, "num_cn": "②", "label": "蒸煮脱胶", "title": "是刈是濩", "desc": "蒸煮葛藤，软化并分解果胶，使纤维易分离"}, {"num": 3, "num_cn": "③", "label": "剥刮韧皮", "title": "取丝", "desc": "剥下葛皮，刮去外层粗皮，得柔韧葛丝"}, {"num": 4, "num_cn": "④", "label": "绩麻成线", "title": "捻接纺纱", "desc": "以纺坠捻接葛丝成连续纱线，为\"绩\""}, {"num": 5, "num_cn": "⑤", "label": "上机织布", "title": "絺 / 绤 分织", "desc": "细者为\"絺\"（精细如纱），粗者为\"绤\"（厚实耐用）"}, {"num": 6, "num_cn": "⑥", "label": "染色/本色", "title": "后处理", "desc": "或保持葛本色，或染成所需色泽，裁剪成衣"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/9Z6WCW29U9", "detail": "https://aka.doubaocdn.com/s/4gKMWbS3q3"},
        "history_note": "史证：《诗经·周南·葛覃》\"葛之覃兮，施于中谷……是刈是濩，为絺为绤\"，即咏葛藤采割、蒸煮、织为粗细两种葛布；浙江钱山漾遗址出土葛布残片距今约4200年，为迄今最早纺织品实物之一。本图为示意流程。",
    },
    "大麻布": {
        "steps": [{"num": 1, "num_cn": "①", "label": "种麻收刈", "title": "种植收割", "desc": "大田种植大麻，适时收割成熟麻秆"}, {"num": 2, "num_cn": "②", "label": "沤麻脱胶", "title": "可以沤麻", "desc": "麻秆浸于池中数日，发酵分解果胶"}, {"num": 3, "num_cn": "③", "label": "剥麻取皮", "title": "取茎皮", "desc": "从麻秆上剥下韧皮，刮去木质残屑"}, {"num": 4, "num_cn": "④", "label": "绩麻成缕", "title": "分劈捻接", "desc": "把纤维分劈、捻接成麻缕（粗条）"}, {"num": 5, "num_cn": "⑤", "label": "纺纱", "title": "纺坠纺车", "desc": "以纺坠或手摇纺车把麻缕纺成均匀纱线"}, {"num": 6, "num_cn": "⑥", "label": "上机织布", "title": "平纹交织", "desc": "经纱上织机、纬纱穿梭，织成平纹麻布"}, {"num": 7, "num_cn": "⑦", "label": "漂洗晾晒", "title": "后处理", "desc": "漂洗去残胶、捶打、晾晒，使布面洁白平整"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/vhfaVUBYk7", "detail": "https://aka.doubaocdn.com/s/oBmu5ZUVt6"},
        "history_note": "史证：《诗经·陈风·东门之池》\"东门之池，可以沤麻\"，即咏沤麻之事；大麻为上古至先秦平民最主要衣料，长沙马王堆一号汉墓出土细麻布残片。本图为示意流程。",
    },
    "苎麻布": {
        "steps": [{"num": 1, "num_cn": "①", "label": "剥麻", "title": "取茎皮", "desc": "收割苎麻后剥取茎部韧皮"}, {"num": 2, "num_cn": "②", "label": "刮青去壳", "title": "刮取青皮", "desc": "刮去茎皮外层青皮硬壳，得白芯纤维"}, {"num": 3, "num_cn": "③", "label": "分丝漂白", "title": "劈丝洗白", "desc": "把纤维分劈成细丝，日晒水洗使之洁白"}, {"num": 4, "num_cn": "④", "label": "绩麻成线", "title": "捻接纺纱", "desc": "以纺坠把苎麻细丝捻接成连续纱线"}, {"num": 5, "num_cn": "⑤", "label": "上浆浆纱", "title": "浆纱增韧", "desc": "纱线上浆，增加强度与光滑度，便于织造"}, {"num": 6, "num_cn": "⑥", "label": "上机织造", "title": "织机成布", "desc": "经纱上织机、纬纱穿梭，织成苎麻布"}, {"num": 7, "num_cn": "⑦", "label": "煮练晒干", "title": "洁白如雪", "desc": "煮练去残胶、日晒漂白，布面洁白挺括"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/vKhOZfVCmh", "detail": "https://aka.doubaocdn.com/s/QNNAZWAyqg"},
        "history_note": "史证：苎麻为中国特产，欧美称\"中国草\"，所织夏布轻薄挺括、透气汗；长沙马王堆一号汉墓出土精细苎麻布残片，反映汉代苎麻纺绩水平。本图为示意流程。",
    },
    "棉布": {
        "steps": [{"num": 1, "num_cn": "①", "label": "采棉", "title": "采摘棉花", "desc": "棉花成熟后采摘棉桃，取洁白棉絮"}, {"num": 2, "num_cn": "②", "label": "轧棉去籽", "title": "搅车轧籽", "desc": "用轧棉搅车挤去棉籽，得净棉"}, {"num": 3, "num_cn": "③", "label": "弹棉松解", "title": "弹弓弹松", "desc": "弓弦弹敲棉絮，使其蓬松松解"}, {"num": 4, "num_cn": "④", "label": "卷条搓棉", "title": "搓成棉条", "desc": "把弹好的棉花搓成细长棉条，备纺"}, {"num": 5, "num_cn": "⑤", "label": "纺纱", "title": "三锭纺车", "desc": "黄道婆式三锭脚踏纺车，把棉条纺成纱"}, {"num": 6, "num_cn": "⑥", "label": "上机织造", "title": "织机成布", "desc": "经纱上织机、纬纱穿梭，织成棉布"}, {"num": 7, "num_cn": "⑦", "label": "漂染印整", "title": "后整理", "desc": "漂白、染色、印花、后整理成成品布"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/QXiz7yJMnm", "detail": "https://aka.doubaocdn.com/s/KpsbO8IAWV"},
        "history_note": "史证：棉花自宋元传入并普及，元代黄道婆革新纺棉工具（三锭脚踏纺车），使松江棉布\"衣被天下\"；明清棉布渐取代麻布成为大众主要衣料。本图为示意流程。",
    },
    "蕉布": {
        "steps": [{"num": 1, "num_cn": "①", "label": "割蕉茎", "title": "取鲜嫩茎皮", "desc": "采割芭蕉茎秆，取茎皮韧皮纤维，须趁鲜嫩"}, {"num": 2, "num_cn": "②", "label": "沤蕉取麻", "title": "浸水脱胶", "desc": "蕉茎皮浸水沤制，分解果胶使纤维分离"}, {"num": 3, "num_cn": "③", "label": "刮青分丝", "title": "刮青劈丝", "desc": "刮去外层青皮，取白色韧皮纤维劈成细丝"}, {"num": 4, "num_cn": "④", "label": "绩麻成线", "title": "绩接成线", "desc": "手捻或纺坠把细丝绩接成均匀纱线"}, {"num": 5, "num_cn": "⑤", "label": "上机织布", "title": "平纹织蕉布", "desc": "整经上机平纹织造，织成清凉透气蕉布"}, {"num": 6, "num_cn": "⑥", "label": "漂洗成布", "title": "轻凉贡品", "desc": "漂洗晾干，布面平整轻凉，历代列为贡品"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/JTGevh6c8Z", "detail": "https://aka.doubaocdn.com/s/hEGgGFx1M9"},
        "history_note": "史证：蕉布以芭蕉茎韧皮纤维经沤制、刮青、绩线、平纹织成，清凉透气、轻薄洁白；南方历代多列为贡品。本图为示意流程。",
    },
    "绢": {
        "steps": [{"num": 1, "num_cn": "①", "label": "养蚕取茧", "title": "育蚕结茧", "desc": "桑叶饲蚕，蚕老熟后吐丝结茧"}, {"num": 2, "num_cn": "②", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中找丝头，抽多根茧丝合成生丝"}, {"num": 3, "num_cn": "③", "label": "络丝", "title": "绕上丝篗", "desc": "把生丝均匀缠绕到丝篗（线框）上"}, {"num": 4, "num_cn": "④", "label": "并丝", "title": "合股加捻", "desc": "把多根细丝合并、略加捻，使丝缕均匀"}, {"num": 5, "num_cn": "⑤", "label": "整经", "title": "排布经纱", "desc": "按幅宽把经纱平行卷绕，排布上织机"}, {"num": 6, "num_cn": "⑥", "label": "平纹素织", "title": "织机成绢", "desc": "经一上一下、纬纱穿梭，平纹素织成绢"}, {"num": 7, "num_cn": "⑦", "label": "练染后整理", "title": "煮练染色", "desc": "煮练脱丝胶、染色、整理，绢面光洁"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/laRyVpV5bI", "detail": "https://aka.doubaocdn.com/s/4uGqb5peex"},
        "history_note": "史证：绢为平纹素织丝织物，是古代最基础的丝织品；战国楚墓、马王堆汉墓均大量出土绢地绣品，凤鸟纹绣绢䋺衣即以紫红绢为地刺绣。本图为示意流程。",
    },
    "纱": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "络丝", "title": "绕上丝篗", "desc": "把生丝均匀缠绕到丝篗（线框）上"}, {"num": 3, "num_cn": "③", "label": "整经", "title": "经纬稀疏排布", "desc": "经纱按稀疏间隔平行卷绕，备织"}, {"num": 4, "num_cn": "④", "label": "平纹疏织", "title": "方孔纱", "desc": "经纬稀疏平纹交织，织出透空方孔"}, {"num": 5, "num_cn": "⑤", "label": "练漂", "title": "煮练漂白", "desc": "煮练脱胶、漂白，纱面洁白轻薄"}, {"num": 6, "num_cn": "⑥", "label": "裁制轻薄单衣", "title": "素纱襌衣", "desc": "裁裁缝成极轻薄的素纱单衣，透而有质"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/SufnUKzo4G", "detail": "https://aka.doubaocdn.com/s/kS5UbSRFO1"},
        "history_note": "史证：纱为经纬稀疏的平纹疏织丝织物，透空呈方孔、轻薄通透；马王堆一号汉墓出土素纱襌衣仅重49克，折叠可入火柴盒，为古代纱织巅峰。本图为示意流程。",
    },
    "縠": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "强捻成绉线", "title": "加捻成紧线", "desc": "把生丝反复加捻，捻得很紧，成绉线"}, {"num": 3, "num_cn": "③", "label": "整经", "title": "排布经纱", "desc": "按幅宽把经纱平行卷绕，排布上织机"}, {"num": 4, "num_cn": "④", "label": "织造", "title": "织机成坯", "desc": "强捻绉线作经纬，织成平整坯绸"}, {"num": 5, "num_cn": "⑤", "label": "练整", "title": "捻缩显绉纹", "desc": "煮练后强捻线收缩，布面自然起绉纹"}, {"num": 6, "num_cn": "⑥", "label": "成轻薄绉纱", "title": "罗縠成品", "desc": "布面绉纹细腻、轻薄飘逸，即罗縠"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/Ld5YkLgbiI", "detail": "https://aka.doubaocdn.com/s/s1YP77hzfh"},
        "history_note": "史证：縠为强捻丝织成的平纹绉纱，煮练后因捻度回缩使布面起绉，轻薄如雾；秦汉罗縠为高档丝织品，与纱、罗并称。本图为示意流程。",
    },
    "罗": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "络丝", "title": "绕上丝篗", "desc": "把生丝均匀缠绕到丝篗（线框）上"}, {"num": 3, "num_cn": "③", "label": "整经", "title": "排布经纱", "desc": "按幅宽把经纱平行卷绕，排布上织机"}, {"num": 4, "num_cn": "④", "label": "绞经提花织造", "title": "两经绞一纬", "desc": "两根经丝相互绞转再穿纬，织出椒孔"}, {"num": 5, "num_cn": "⑤", "label": "练染", "title": "煮练染色", "desc": "煮练脱胶、染色，罗面光洁"}, {"num": 6, "num_cn": "⑥", "label": "轻薄透气成衣", "title": "夏衣罗衫", "desc": "裁成透气轻薄的罗衫，夏日穿着凉爽"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/QeIiyry4ZA", "detail": "https://aka.doubaocdn.com/s/iQCpXUjXuK"},
        "history_note": "史证：罗为绞经丝织物，两根经丝相互绞转再穿纬，织出稳定椒孔、轻薄透气；汉唐罗为高档夏季衣料，\"罗衫\"\"越罗\"著称。本图为示意流程。",
    },
    "绮": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "染色", "title": "先染丝线", "desc": "把生丝先染成所需颜色，备织"}, {"num": 3, "num_cn": "③", "label": "整经", "title": "排布经纱", "desc": "按幅宽把染色经纱平行卷绕上织机"}, {"num": 4, "num_cn": "④", "label": "提花织造", "title": "平纹地斜纹显花", "desc": "提花机上平纹为地、斜纹起花，织出暗花绮"}, {"num": 5, "num_cn": "⑤", "label": "练染", "title": "后整理", "desc": "煮练整理、固色，使绮面光洁花明"}, {"num": 6, "num_cn": "⑥", "label": "裁制衣袍", "title": "文绮衣袍", "desc": "裁成暗花绮袍，华贵而不艳俗"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/jTkOg1Mf4V", "detail": "https://aka.doubaocdn.com/s/2P7EF4wv57"},
        "history_note": "史证：绮为平纹地、斜纹显花的提花丝织物，多为单色暗花（文绮），汉代盛行；与多彩织锦不同，绮以同一色丝借组织变化显出花纹。本图为示意流程。",
    },
    "经锦": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "染色分色", "title": "染成多色", "desc": "把丝线分别染成朱红、藏青、金黄等色"}, {"num": 3, "num_cn": "③", "label": "多色经线排经", "title": "按纹样排经", "desc": "按锦面纹样把各色经线分组排好上织机"}, {"num": 4, "num_cn": "④", "label": "重经提花织造", "title": "经线显花", "desc": "提花机提起多组彩色经线，织出彩锦花纹"}, {"num": 5, "num_cn": "⑤", "label": "练整", "title": "后整理", "desc": "煮练整理、绷紧，使锦面平整色彩鲜明"}, {"num": 6, "num_cn": "⑥", "label": "裁锦成衣", "title": "锦袍用品", "desc": "裁成锦袍，或织成绶带、香囊等用品"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/NMbXcwNKMR", "detail": "https://aka.doubaocdn.com/s/9DSiEV9s9V"},
        "history_note": "史证：经锦以多组彩色经线显花、纬线单色，是战国至汉织锦的主流（如\"韩仁锦\"\"登高明望四海锦\"）；唐以后渐为纬锦取代。本图为示意流程。",
    },
    "纬锦": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "染色分色", "title": "染成多色", "desc": "把丝线染成朱、绿、蓝、金等多种颜色"}, {"num": 3, "num_cn": "③", "label": "重纬提花织造", "title": "通经回纬显花", "desc": "经线单色打底，彩色纬线换色织出花纹"}, {"num": 4, "num_cn": "④", "label": "彩纬配色", "title": "按纹样换色", "desc": "织到不同部位换不同彩纬，配色显花纹"}, {"num": 5, "num_cn": "⑤", "label": "练整", "title": "后整理", "desc": "煮练整理、绷紧，使锦面平整色彩鲜明"}, {"num": 6, "num_cn": "⑥", "label": "裁锦成衣", "title": "唐锦袍服", "desc": "裁成色彩富丽的唐锦袍服或幡毯"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/86EdL2o0VF", "detail": "https://aka.doubaocdn.com/s/D7rKliOSxh"},
        "history_note": "史证：纬锦以彩色纬线显花、经线单色，换色灵活、色彩更富丽，唐代盛行取代经锦；唐锦多为斜纹纬锦。本图为示意流程。",
    },
    "绫": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "络丝", "title": "绕上丝篗", "desc": "把生丝均匀缠绕到丝篗（线框）上"}, {"num": 3, "num_cn": "③", "label": "整经", "title": "排布经纱", "desc": "按幅宽把经纱平行卷绕，排布上织机"}, {"num": 4, "num_cn": "④", "label": "斜纹起花织造", "title": "经纬浮线显花", "desc": "斜纹组织、经纬浮线交织，织出斜纹绫"}, {"num": 5, "num_cn": "⑤", "label": "练染", "title": "煮练染色", "desc": "煮练脱胶、染色，绫面光滑有光"}, {"num": 6, "num_cn": "⑥", "label": "成衣或装裱用料", "title": "绫衣与裱画", "desc": "裁成绫衣，或作书画装裱绫边"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/NUaZJUgYyI", "detail": "https://aka.doubaocdn.com/s/mHCvZg3DRc"},
        "history_note": "史证：绫为斜纹组织丝织物，经纬浮线交织使表面起斜向纹路（冰凌纹），光滑柔软有光泽；唐绫盛行，用作官服与书画装裱。本图为示意流程。",
    },
    "宋锦": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "染丝配色", "title": "丝线染色", "desc": "经丝染成地色，纬丝染成雅彩配色"}, {"num": 3, "num_cn": "③", "label": "整经", "title": "排布经纱", "desc": "按幅宽把经纱平行卷绕，排布上织机"}, {"num": 4, "num_cn": "④", "label": "彩纬提花织造", "title": "经斜纹地彩纬花", "desc": "斜纹为地、彩色纬线提花，织出宋锦"}, {"num": 5, "num_cn": "⑤", "label": "挖花配色", "title": "局部换色", "desc": "纹样局部挖花、换彩纬，配色典雅"}, {"num": 6, "num_cn": "⑥", "label": "练整", "title": "后整理", "desc": "煮练整理、绷紧，使锦面平整古朴"}, {"num": 7, "num_cn": "⑦", "label": "装裱 / 袍料", "title": "宋锦用途", "desc": "用作书画装裱锦绫，或裁成袍服料"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/FVeFCPDDl2", "detail": "https://aka.doubaocdn.com/s/dz61wGonw2"},
        "history_note": "史证：宋锦（宋式锦）经纬皆丝、经斜纹地、彩纬提花，并以挖花配色局部换色，风格典雅古朴；与云锦华丽相对，多用于书画装裱与袍服。本图为示意流程。",
    },
    "纳石失": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "打金箔", "title": "锤打成箔", "desc": "匠人反复锤打金块，打成极薄金箔"}, {"num": 3, "num_cn": "③", "label": "切金线", "title": "金箔切丝", "desc": "把金箔切成极细的扁平金线"}, {"num": 4, "num_cn": "④", "label": "金线并丝", "title": "纸胎裹金", "desc": "把金线裹在丝线或纸胎上，成圆金线"}, {"num": 5, "num_cn": "⑤", "label": "整经", "title": "排布经纱", "desc": "按幅宽把经丝平行卷绕，排布上织机"}, {"num": 6, "num_cn": "⑥", "label": "金线入纬织造", "title": "织金显花", "desc": "把金线作纬织入，织出金光闪闪的锦纹"}, {"num": 7, "num_cn": "⑦", "label": "练整成锦", "title": "纳石失成锦", "desc": "整理绷紧，金光熠熠的织金锦即成"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/TpujRUaDIA", "detail": "https://aka.doubaocdn.com/s/U2CURluNGx"},
        "history_note": "史证：纳石失为波斯语 nasij 音译，即元代织金锦；以片金（金箔切条，常裹于纸/丝胎）作纬织入，金光富丽，为蒙古贵族袍服所用，由官府织金局织造。本图为示意流程。",
    },
    "云锦": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "染丝", "title": "丝线染色", "desc": "把生丝染成所需各种彩色地纬"}, {"num": 3, "num_cn": "③", "label": "捻金/片金/孔雀羽线", "title": "备特殊线材", "desc": "打制捻金、片金线，并取孔雀羽丝捻线"}, {"num": 4, "num_cn": "④", "label": "整经上机", "title": "大花楼织机", "desc": "经丝排好，上高大花楼提花织机"}, {"num": 5, "num_cn": "⑤", "label": "妆花挖花盘织", "title": "挖花盘织", "desc": "楼上拽花工提花，楼下织手挖花盘织彩纬"}, {"num": 6, "num_cn": "⑥", "label": "织金显色", "title": "金翠交辉", "desc": "金线织入显金，孔雀羽线显翠，富丽斑斓"}, {"num": 7, "num_cn": "⑦", "label": "练整成锦", "title": "云锦成锦", "desc": "整理绷紧，云霞灿烂的云锦即成"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/ncjYeOvU1r", "detail": "https://aka.doubaocdn.com/s/MGxZm27lXd"},
        "history_note": "史证：云锦为明清南京织锦代表，用大花楼提花机，集妆花、织金、孔雀羽线三大工艺于一身，\"织金妆花\"，云霞灿烂，为皇家御用。本图为示意流程。",
    },
    "缎": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "络丝", "title": "绕上丝篗", "desc": "把生丝均匀缠绕到丝篗（线框）上"}, {"num": 3, "num_cn": "③", "label": "整经", "title": "排布经纱", "desc": "按幅宽把经纱平行卷绕，排布上织机"}, {"num": 4, "num_cn": "④", "label": "缎纹组织织造", "title": "浮长显光", "desc": "缎纹组织、浮线长，织出光滑缎坯"}, {"num": 5, "num_cn": "⑤", "label": "练染", "title": "煮练染色", "desc": "煮练脱胶、染色，缎坯光洁"}, {"num": 6, "num_cn": "⑥", "label": "后整理（碾光）", "title": "碾石压光", "desc": "用碾石在缎面上反复碾压，压出缎光"}, {"num": 7, "num_cn": "⑦", "label": "成衣", "title": "缎袍缎袄", "desc": "裁成光滑亮丽的缎面袍服"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/obnbAdMVsX", "detail": "https://aka.doubaocdn.com/s/e1ixIzQVnL"},
        "history_note": "史证：缎为缎纹组织丝织物，经纬浮线长、表面光滑明亮；元明以后盛行，与绸并称\"绸缎\"，碾光后缎光莹润。本图为示意流程。",
    },
    "缂丝": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "热水煮茧抽丝", "desc": "茧浸热水锅中，抽多根茧丝合成生丝"}, {"num": 2, "num_cn": "②", "label": "染丝配色", "title": "丝线染彩", "desc": "把纬丝染成画稿所需各种颜色"}, {"num": 3, "num_cn": "③", "label": "排经线", "title": "木棦排经", "desc": "在木制织机（木棦）上排好细经丝"}, {"num": 4, "num_cn": "④", "label": "通经断纬挖织", "title": "小梭逐色", "desc": "经线贯通，彩色小梭按色块逐色挖织换色"}, {"num": 5, "num_cn": "⑤", "label": "修整显花纹", "title": "修整成像", "desc": "修整轮廓、补色，使花纹如雕镂立体"}, {"num": 6, "num_cn": "⑥", "label": "缂织成幅", "title": "缂丝成幅", "desc": "织成一幅缂丝，可摹书画、做袍面"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/F99mghZkCt", "detail": "https://aka.doubaocdn.com/s/NAGxOE8Xnz"},
        "history_note": "史证：缂丝为\"通经断纬\"织法，以彩色小梭按画稿色块逐色挖织换色，承空观之如雕镂；唐宋以来多摹缂名家书画，极珍贵，有\"一寸缂丝一寸金\"之说。本图为示意流程。",
    },
    "漳绒": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "备地经绒经", "desc": "煮茧抽丝，地经作布地，绒经较粗作绒面"}, {"num": 2, "num_cn": "②", "label": "整经", "title": "分别上机", "desc": "地经与绒经分别整经，绒经用绒综控制"}, {"num": 3, "num_cn": "③", "label": "上机起绒", "title": "垫杆起绒圈", "desc": "绒经下垫细金属杆，织过后顶起成绒圈"}, {"num": 4, "num_cn": "④", "label": "割绒显绒", "title": "割圈成绒毛", "desc": "利刀沿杆顶割开绒圈成绒毛；花部割、素部留"}, {"num": 5, "num_cn": "⑤", "label": "梳刷整绒", "title": "梳理直立", "desc": "刷梳绒毛使直立平整，去浮绒杂丝"}, {"num": 6, "num_cn": "⑥", "label": "练染成绒", "title": "染深色成绒", "desc": "练染玄青酱绛等深色，成丝绒袍料"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/aK5VI55l23", "detail": "https://aka.doubaocdn.com/s/x5lKxeMroS"},
        "history_note": "史证：漳绒起于福建漳州，以地经、绒经交织，垫金属杆起绒圈再割绒成绒毛；花漳绒花部割绒、素部不割，绒地相间如浮雕。清代高级绒面袍料。本图为示意流程。",
    },
    "妆花缎": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "煮茧抽丝", "desc": "煮茧缫丝，备足经线、纬线及彩丝"}, {"num": 2, "num_cn": "②", "label": "染丝配色", "title": "分色备丝", "desc": "按画稿染出大红、石青、赤金等各色丝"}, {"num": 3, "num_cn": "③", "label": "整经上机", "title": "大花楼织机", "desc": "整经上大花楼木织机，挂好花本"}, {"num": 4, "num_cn": "④", "label": "缎纹地织造", "title": "织缎地", "desc": "先织出光滑的缎纹地组织为底"}, {"num": 5, "num_cn": "⑤", "label": "妆花挖花盘织", "title": "彩纬挖花", "desc": "用小梭按画稿逐色挖花盘织、配色晕染"}, {"num": 6, "num_cn": "⑥", "label": "织金显色", "title": "金线织花", "desc": "以金线织花纹轮廓，金彩交辉显华贵"}, {"num": 7, "num_cn": "⑦", "label": "练整成缎", "title": "妆花缎成", "desc": "练丝碾光，成富丽堂皇的妆花缎匹"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/Vupj8wraNG", "detail": "https://aka.doubaocdn.com/s/yGllGzqN6Z"},
        "history_note": "史证：妆花缎为南京云锦最高品种，明清御用；用大花楼木织机两人合作（楼上拽花、楼下织造），以彩纬挖花盘织、织金显色，配色富丽。本图为示意流程。",
    },
    "库缎": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "丝细匀光洁", "desc": "缫取细匀光洁蚕丝，为平滑缎面打基础"}, {"num": 2, "num_cn": "②", "label": "染丝", "title": "配色稳重", "desc": "经丝染色，青、蓝、绛、玄为主"}, {"num": 3, "num_cn": "③", "label": "整经上机", "title": "大花楼", "desc": "大花楼织机整经，缎地经密较高"}, {"num": 4, "num_cn": "④", "label": "缎纹地织造", "title": "平滑光亮", "desc": "缎纹组织织地，经纬浮长长，缎面光亮"}, {"num": 5, "num_cn": "⑤", "label": "提花显纹", "title": "花/素库缎", "desc": "提花织花卉八宝缠枝（花库缎）或素面（素库缎）"}, {"num": 6, "num_cn": "⑥", "label": "织金", "title": "妆金库缎", "desc": "织入金线勾勒花纹，金光闪耀，供宫廷礼服"}, {"num": 7, "num_cn": "⑦", "label": "练整成缎", "title": "缎面平整", "desc": "练整熨平，缎面平整、花地分明，入库供御"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/isjftU22mC", "detail": "https://aka.doubaocdn.com/s/R0MlLULL32"},
        "history_note": "史证：库缎为江宁织造所织御用缎，织成后入库供宫廷使用，故名\"库缎\"；分花库缎、素库缎，妆金库缎织金供礼服，缎面平滑光亮。本图为示意流程。",
    },
    "蜀锦": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "合股均匀", "desc": "煮茧抽丝合股，丝量足、均匀，为厚重锦地打基础"}, {"num": 2, "num_cn": "②", "label": "染丝分色", "title": "艳而不俗", "desc": "经纬分色染，红黄蓝绿相配，间用金银色"}, {"num": 3, "num_cn": "③", "label": "整经", "title": "多色排经", "desc": "按纹样循环整经，多色经线按花排成组"}, {"num": 4, "num_cn": "④", "label": "提花织造", "title": "经锦/纬锦显花", "desc": "汉重经显花，唐兼用重纬，织团窠连珠大花"}, {"num": 5, "num_cn": "⑤", "label": "练整", "title": "去胶熨整", "desc": "练丝去胶、熨平，锦面平整色彩焕发"}, {"num": 6, "num_cn": "⑥", "label": "裁锦贸易", "title": "成衣/贡赋", "desc": "裁衣袍衾褥，亦为贡赋贸易商品，远销丝路"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/mxqKVa5sqj", "detail": "https://aka.doubaocdn.com/s/iuJhXx2bx5"},
        "history_note": "史证：蜀锦产于成都，汉设锦官；汉蜀锦为经锦，唐蜀锦兼用纬锦，多团窠连珠纹；诸葛亮言\"决敌之资，唯仰锦耳\"，蜀锦为当时重要财政与外贸商品。本图为示意流程。",
    },
    "纨": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "极细丝少合股", "desc": "取极细茧丝，少合股缫制，丝缕纤细均匀"}, {"num": 2, "num_cn": "②", "label": "络丝", "title": "理直绕框", "desc": "细丝理直去糙，绕框备用，惜丝如惜金"}, {"num": 3, "num_cn": "③", "label": "整经", "title": "高经密", "desc": "大幅提高经密，经纬细密排布备织"}, {"num": 4, "num_cn": "④", "label": "平纹细织", "title": "密织如霜雪", "desc": "平纹极密交织，打纬密实，几不见孔隙"}, {"num": 5, "num_cn": "⑤", "label": "练染", "title": "去胶增白", "desc": "练丝去胶增白，纨多保持素白\"纨素\""}, {"num": 6, "num_cn": "⑥", "label": "成衣/扇面", "title": "纨衣纨扇", "desc": "制纨衣纨裤巾帕，亦作纨扇扇面"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/IcnbFvbznI", "detail": "https://aka.doubaocdn.com/s/sN4AG5Iqhw"},
        "history_note": "史证：纨为极细密平纹白绢，经纬极密、色白如霜雪，称\"纨素\"；可制纨衣纨裤（纨绔子弟），亦作纨扇（团扇）扇面。本图为示意流程。",
    },
    "绸": {
        "steps": [{"num": 1, "num_cn": "①", "label": "缫丝", "title": "粗细分织", "desc": "煮茧抽丝，粗丝织粗绸、细丝织细绸"}, {"num": 2, "num_cn": "②", "label": "络丝", "title": "理直绕框", "desc": "丝理直去糙，绕框备用"}, {"num": 3, "num_cn": "③", "label": "整经", "title": "排经上机", "desc": "按绸面密度把经线上排整齐上机"}, {"num": 4, "num_cn": "④", "label": "织造", "title": "平纹/斜纹", "desc": "平纹织纺绸春绸、斜纹织漳缎，绸面平整光滑"}, {"num": 5, "num_cn": "⑤", "label": "练染", "title": "染色印花", "desc": "练丝去胶，再染色或印花，色泽亮丽"}, {"num": 6, "num_cn": "⑥", "label": "成绸", "title": "丝物通称", "desc": "平整柔滑，作衣袍衬里被面旗帜，绸成丝织物通称"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/e7WrltOLeB", "detail": "https://aka.doubaocdn.com/s/4B0bt0gTxO"},
        "history_note": "史证：绸为平纹或斜纹素地丝织物，练染后平整柔滑；明清以降\"绸\"成为丝织物通称，广泛作衣袍、衬里、被面、旗帜。本图为示意流程。",
    },
    "茧绸": {
        "steps": [{"num": 1, "num_cn": "①", "label": "放养采茧", "title": "柞林放养", "desc": "柞蚕野外放于柞林食柞叶，结黄褐硬茧后采收"}, {"num": 2, "num_cn": "②", "label": "缫丝", "title": "柞丝粗硬", "desc": "柞蚕茧缫丝，丝粗硬、色本黄褐，合股成缕"}, {"num": 3, "num_cn": "③", "label": "络丝", "title": "理直绕框", "desc": "柞丝理直去糙绕框，韧性强不易断"}, {"num": 4, "num_cn": "④", "label": "整经", "title": "排经上机", "desc": "按绸面密度把经线上排整齐上机"}, {"num": 5, "num_cn": "⑤", "label": "织造", "title": "坚韧厚实", "desc": "平纹或斜纹织造，本色黄褐，坚韧有天然光泽"}, {"num": 6, "num_cn": "⑥", "label": "煮练/染色", "title": "多留本色", "desc": "可煮练脱胶增柔或染色，多留本黄褐"}, {"num": 7, "num_cn": "⑦", "label": "成绸", "title": "出口名品", "desc": "坚牢耐穿吸湿透气，山东昌邑茧绸远销海外"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/FOcT5eeiGy", "detail": "https://aka.doubaocdn.com/s/SOKvSLM58Y"},
        "history_note": "史证：茧绸以柞蚕丝织成，柞蚕野外放养于柞林，丝粗硬、本色黄褐；绸坚韧厚实、吸湿透气，山东昌邑茧绸明清时远销海外。本图为示意流程。",
    },
    "兽皮": {
        "steps": [{"num": 1, "num_cn": "①", "label": "狩猎取皮", "title": "猎取野兽", "desc": "入山林猎取狐貂羊鹿等，取得整皮"}, {"num": 2, "num_cn": "②", "label": "剥皮", "title": "整张剥取", "desc": "从兽体上整张剥下皮张，除去残肉"}, {"num": 3, "num_cn": "③", "label": "浸水软化", "title": "泡水回软", "desc": "把干皮浸入水中，使之回软洁净"}, {"num": 4, "num_cn": "④", "label": "去脂刮里", "title": "刮净肉里", "desc": "用刮刀把皮里油脂、残肉刮净"}, {"num": 5, "num_cn": "⑤", "label": "鞣制", "title": "耐水不腐", "desc": "用树皮、栲胶等揉制，使皮耐水不腐"}, {"num": 6, "num_cn": "⑥", "label": "裁剪", "title": "按样裁皮", "desc": "按衣样把鞣好的皮张裁剪成片"}, {"num": 7, "num_cn": "⑦", "label": "缝缀成裘衣", "title": "缝成裘衣", "desc": "把皮片缝缀成保暖的裘皮大衣"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/D4ittLNEZF", "detail": "https://aka.doubaocdn.com/s/Ua9Uy38xHi"},
        "history_note": "史证：上古先民以兽皮为衣，经剥皮、刮里、鞣制后缝缀成裘；鞣制以树皮、栲胶等植物鞣料揉皮，使生皮变为耐水不腐、柔软耐用的熟皮。本图为示意流程。",
    },
    "毛毡": {
        "steps": [{"num": 1, "num_cn": "①", "label": "剪毛", "title": "从羊剪毛", "desc": "从羊身上剪下羊毛，取净毛"}, {"num": 2, "num_cn": "②", "label": "洗毛去脂", "title": "洗净油脂", "desc": "在水中洗涤羊毛，去脂去污垢"}, {"num": 3, "num_cn": "③", "label": "弹松", "title": "弹松羊毛", "desc": "用弓弦把羊毛弹松蓬松"}, {"num": 4, "num_cn": "④", "label": "铺毛成层", "title": "平铺成层", "desc": "把弹松的羊毛在竹帘上铺成均匀薄层"}, {"num": 5, "num_cn": "⑤", "label": "喷水加温", "title": "喷水加热", "desc": "在毛层上喷温水，使羊毛湿润加温"}, {"num": 6, "num_cn": "⑥", "label": "压挤毡合", "title": "反复搓压", "desc": "卷起竹帘反复搓压，羊毛鳞片互锁毡合"}, {"num": 7, "num_cn": "⑦", "label": "整形晾干", "title": "成毡", "desc": "整成方幅、晾干，毛毡即成"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/rfOJBk6nWe", "detail": "https://aka.doubaocdn.com/s/6v30U6B4Pw"},
        "history_note": "史证：毛毡不经纺织，靠羊毛鳞片在温水加压下互锁毡缩而成；游牧民族早用以制毡毯、毡帽、毡帐（穹庐）。本图为示意流程。",
    },
    "毛罽": {
        "steps": [{"num": 1, "num_cn": "①", "label": "剪毛", "title": "剪取毛驼毛", "desc": "从羊、驼身上剪取羊毛、驼毛"}, {"num": 2, "num_cn": "②", "label": "洗毛去脂", "title": "洗净油脂", "desc": "在水中洗涤毛纤维，去脂去垢"}, {"num": 3, "num_cn": "③", "label": "弹梳", "title": "弹梳成条", "desc": "弹松、梳栉，把毛理成均匀毛条"}, {"num": 4, "num_cn": "④", "label": "纺纱", "title": "纺成毛纱", "desc": "用纺车把毛条纺成结实毛纱"}, {"num": 5, "num_cn": "⑤", "label": "上机粗纺织造", "title": "织成毛坯", "desc": "毛纱上织机，粗纺交织成毛坯布"}, {"num": 6, "num_cn": "⑥", "label": "缩绒", "title": "温水缩绒", "desc": "毛坯经温水揉搓缩绒，纤维交织厚实"}, {"num": 7, "num_cn": "⑦", "label": "整理成厚实毛布", "title": "毛罽成布", "desc": "整幅、晾干，成厚实保暖的毛罽"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/kuIrSGlEHt", "detail": "https://aka.doubaocdn.com/s/sfXDBHn6b0"},
        "history_note": "史证：毛罽为羊毛/驼毛纺成纱后上机织、再经缩绒的厚实毛织物，比毡细密；汉唐多自西域传入，作地毯、衣料、褥垫。本图为示意流程。",
    },
    "氆氇": {
        "steps": [{"num": 1, "num_cn": "①", "label": "剪毛", "title": "剪取细毛", "desc": "从藏羊身上剪下细软羊毛"}, {"num": 2, "num_cn": "②", "label": "洗毛", "title": "洗净羊毛", "desc": "在河水中洗涤羊毛，去脂去垢"}, {"num": 3, "num_cn": "③", "label": "梳毛", "title": "梳成细条", "desc": "用梳毛栉把细毛梳成均匀毛条"}, {"num": 4, "num_cn": "④", "label": "纺纱", "title": "纺细毛纱", "desc": "用纺车把细毛条纺成细密毛纱"}, {"num": 5, "num_cn": "⑤", "label": "上机细织", "title": "织成细坯", "desc": "毛纱上织机，细密交织成氆氇坯"}, {"num": 6, "num_cn": "⑥", "label": "染色", "title": "染色彩条", "desc": "把氆氇染成藏蓝、绯红等条纹色"}, {"num": 7, "num_cn": "⑦", "label": "缩绒碾光", "title": "缩绒碾光", "desc": "缩绒后碾石压光，氆氇密实光洁"}, {"num": 8, "num_cn": "⑧", "label": "裁制藏袍", "title": "藏袍邦典", "desc": "裁成藏袍，或织成邦典彩条围裙"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/NQULdUZV4h", "detail": "https://aka.doubaocdn.com/s/cqWylsVpMI"},
        "history_note": "史证：氆氇为西藏吐蕃以来的细羊毛手工织品，细密柔软、保暖耐用；藏族用以裁制藏袍、邦典（彩条围裙），是藏地传统衣料。本图为示意流程。",
    },
    "褐": {
        "steps": [{"num": 1, "num_cn": "①", "label": "取粗毛/粗麻", "title": "粗韧耐穿", "desc": "取粗羊毛或粗麻纤维，不择精良，取其粗韧"}, {"num": 2, "num_cn": "②", "label": "洗/沤", "title": "去脂脱胶", "desc": "羊毛洗毛去脂，或麻料沤麻脱胶"}, {"num": 3, "num_cn": "③", "label": "弹理", "title": "粗粗梳理", "desc": "弹松纤维、粗梳去杂，不求精细"}, {"num": 4, "num_cn": "④", "label": "纺粗纱", "title": "捻松不匀", "desc": "纺成粗纱，捻度较松、粗细不匀亦无妨"}, {"num": 5, "num_cn": "⑤", "label": "粗织", "title": "粗硬厚实", "desc": "上机平纹或粗斜纹，织成粗硬厚实褐布"}, {"num": 6, "num_cn": "⑥", "label": "成褐布", "title": "贫者之衣", "desc": "色褐质粗，贫者裹身衣被；\"释褐\"由此引申"}],
        "images": {"overview": "https://aka.doubaocdn.com/s/nKlp240nlH", "detail": "https://aka.doubaocdn.com/s/UM2TuKC8T6"},
        "history_note": "史证：褐为粗毛或粗麻织的粗衣，不求精细、粗韧耐穿，古多为贫者所服（\"短褐\"）；\"释褐\"即脱去布衣入仕。本图为示意流程。",
    },
}

# 数据库面料名 → 素材名 别名映射（库内名称与素材包名称不一致时）
NAME_ALIAS = {"兽皮毛皮": "兽皮"}
