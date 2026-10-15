"""演示数据模式：SQLite 自动建表 + 种子数据（与 database/init.sql 同源）

启用方式：backend/.env 中设置 USE_DEMO_DATA=true。
正式环境仍使用 MySQL 8.0（init.sql），演示模式仅为免安装快速演示。
"""
import json

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.database import Base, engine, SessionLocal
from app.db.models import (
    Users, Costumes, CostumeRelations, Patterns, Relics, PatternTemplates,
    PatternConstraintRules, News, ForumBoards, ForumPosts, ForumReplies,
    Questions, Answers,
)

BOARDS = [
    ("形制溯源", "历代服饰形制考据与史料溯源讨论"),
    ("复原作品", "版型工坊复原作品分享与点评"),
    ("纹样文创", "传统纹样应用与文创设计交流"),
    ("史料求助", "求问服饰史料、文献与考古资料"),
    ("保护行动", "传统服饰文化传播与保护行动"),
]

RELICS = [
    ("马王堆素纱单衣", "秦汉", "湖南长沙", 28.21, 112.97, "湖南博物院", "西汉早期素纱单衣，重仅49克，迄今所见最轻丝织衣物"),
    ("黄昇墓出土褙子", "宋", "福建福州", 26.08, 119.30, "福建省博物馆", "南宋贵族女子服饰，出土大量罗、纱织物与纹样"),
    ("定陵织金妆花缎", "明", "北京昌平", 40.30, 116.22, "明十三陵博物馆", "明万历帝后织金妆花缎龙袍，织造工艺登峰造极"),
    ("敦煌供养人像壁画", "隋唐", "甘肃敦煌", 40.04, 94.81, "敦煌研究院", "唐代供养人服饰形象，反映大袖襦裙与圆领袍"),
    ("集宁路织金锦", "元", "内蒙古集宁", 41.03, 113.11, "内蒙古博物院", "元代纳石失（织金锦）实物，见证丝路织造交流"),
    ("马山一号楚墓丝袍", "先秦", "湖北荆州", 30.35, 112.19, "荆州博物馆", "战国楚墓出土丝织品，深衣形制实证"),
]

COSTUMES = [
    ("深衣", "先秦", "袍服", "士大夫", "文献", "丝·麻·褐", "黻纹·回纹", "玄纁", "《礼记·深衣》所载交领右衽长衣，短毋见肤长毋被土", 6),
    ("素纱单衣", "秦汉", "袍服", "贵族女性", "出土", "素纱", "云气纹", "素白", "马王堆出土，重49克，汉代轻纱工艺巅峰", 1),
    ("曲裾深衣", "秦汉", "下裳", "贵族", "出土", "缣·绮", "云气纹", "尚红", "汉代曲裾绕襟，等级标识鲜明", 1),
    ("宽衫大袖", "魏晋", "袍服", "名士", "图像", "纱·罗", "忍冬纹", "素白", "《洛神赋图》宽衣博带之姿，玄学审美", None),
    ("大袖襦裙", "隋唐", "下裳", "宫廷女性", "图像", "锦·绫·纱", "宝相花", "绯红", "《簪花仕女图》典型唐代女性盛装", 4),
    ("圆领袍", "隋唐", "袍服", "官员", "图像", "绫·罗", "联珠纹", "明黄", "胡服改制的唐代官服常制", 4),
    ("褙子", "宋", "袍服", "女子", "出土", "罗·纱·绢", "折枝花", "天水碧", "直领对襟两侧开衩，宋代典型外衣", 2),
    ("质孙服", "元", "袍服", "蒙古贵族", "文献", "纳石失", "八宝纹", "金·蓝", "元代宫廷一色服制，织金锦为贵", 5),
    ("马面裙", "明", "下裳", "女性", "出土", "妆花缎", "缠枝莲", "正色", "两侧打褶前后裙门平整，明代典型裙式", 3),
    ("旗装", "清", "袍服", "满族女性", "传世", "绸·缎·缂丝", "团花纹", "宝蓝", "清代旗装立领盘扣，满汉服饰并存", None),
]

RELATIONS = [
    (1, "朝代", "先秦", "《礼记·深衣》"),
    (1, "礼制", "深衣之制", "《礼记》"),
    (5, "朝代", "隋唐", "《簪花仕女图》"),
    (5, "纹样", "宝相花", "敦煌壁画"),
    (5, "面料", "锦绫纱", "唐墓壁画"),
    (7, "朝代", "宋", "《东京梦华录》"),
    (7, "纹样", "折枝花", "黄昇墓出土实物"),
    (7, "面料", "罗纱绢", "福建黄昇墓"),
    (9, "朝代", "明", "《明史·舆服志》"),
    (9, "纹样", "缠枝莲", "定陵出土"),
    (9, "面料", "妆花缎", "定陵织金妆花缎"),
    (9, "礼制", "裙式等级", "《明史·舆服志》"),
]

TEMPLATES = [
    (7, "宋", "褙子基准版型",
     '{"points":[{"name":"shoulder","x":20,"y":12},{"name":"collar","x":45,"y":5},{"name":"hem","x":24,"y":78},{"name":"cuff","x":72,"y":30},{"name":"waist","x":38,"y":45}],"params":{"len":60,"sleeve":60,"waist":40,"collar":50}}',
     '{"len":{"min":50,"max":85},"sleeve":{"min":45,"max":80}}', "黄昇墓出土褙子实物测量"),
    (5, "隋唐", "大袖衫基准版型",
     '{"points":[{"name":"shoulder","x":20,"y":12},{"name":"collar","x":45,"y":5},{"name":"hem","x":24,"y":75},{"name":"cuff","x":80,"y":26},{"name":"waist","x":38,"y":45}],"params":{"len":55,"sleeve":80,"waist":40,"collar":50}}',
     '{"len":{"min":40,"max":78},"sleeve":{"min":60,"max":96}}', "《簪花仕女图》大袖形制"),
    (9, "明", "马面裙基准版型",
     '{"points":[{"name":"shoulder","x":20,"y":12},{"name":"collar","x":45,"y":5},{"name":"hem","x":30,"y":85},{"name":"cuff","x":65,"y":25},{"name":"waist","x":35,"y":40}],"params":{"len":70,"sleeve":60,"waist":35,"collar":40}}',
     '{"len":{"min":55,"max":90},"waist":{"min":25,"max":45}}', "定陵出土马面裙实物"),
]

RULES = [
    ("宋", "褙子", '{"len":{"min":50,"max":85,"ref":"宋代褙子及膝至足，见黄昇墓实物"},"sleeve":{"min":45,"max":80,"ref":"宋代袖型较唐收敛"}}', "黄昇墓出土报告"),
    ("隋唐", "大袖衫", '{"len":{"min":40,"max":78,"ref":"唐代襦裙裙长及地"},"sleeve":{"min":60,"max":96,"ref":"唐代大袖衫广袖为典型"}}', "《簪花仕女图》"),
    ("明", "马面裙", '{"len":{"min":55,"max":90,"ref":"明代袄裙长度规范"},"waist":{"min":25,"max":45,"ref":"裙腰比例"}}', "定陵实物"),
]

PATTERNS = [
    ("宝相花", "隋唐", "象征圆满吉祥，佛教艺术与丝绸纹样融合", "敦煌壁画"),
    ("折枝花", "宋", "宋代写生自然之美，清雅含蓄", "黄昇墓"),
    ("缠枝莲", "明", "连绵不绝，寓意生生不息", "定陵织金缎"),
    ("海水江崖", "明", "江山永固，等级尊贵", "明清官服"),
    ("团花纹", "清", "圆满和谐，宫廷常用", "清代传世服饰"),
]

NEWS = [
    ("湖南博物院首次动态呈现西汉素纱单衣数字孪生",
     "AI 数字孪生复原西汉丝绵袍穿着效果；赭黄色印花敷彩再现织物垂坠质感；马王堆丝织文物数字化取得突破。",
     "文博在线", "秦汉", "素纱单衣", 1, "/images/news_susha.png",
     "西汉直裾素纱襌衣1972年出土于长沙马王堆一号汉墓，现藏湖南博物院。衣长128厘米、通袖长195厘米、重仅49克，是迄今所见最轻薄的汉代丝织物。\n"
     "襌衣以精缫蚕丝织造，采用单经单纬交织的方孔平纹，丝缕极细、轻盈精湛；除领口袖口以织锦镶边外，衣身素面无衬里、不加颜色，出土遣册因之称为素纱襌衣。\n"
     "面料来自汉代培育的三眠蚕，吐丝仅10.2至11.3旦，织成后需经煮练、捣练与熨烫方可裁剪。该文物属中国首批禁止出国（境）展览文物。",
     ["秦汉时期服饰形制有什么典型特征？", "素纱襌衣为何能薄如蝉翼？", "如何区分正统素纱单衣复原与现代影楼装？"]),
    ("敦煌服饰研究展再现唐代供养人衣冠",
     "展览集中呈现敦煌壁画中的唐代服饰；大袖襦裙与圆领袍形制成为焦点；数字化复原让壁画人物“走”出洞窟。",
     "敦煌研究院", "隋唐", "大袖襦裙,圆领袍", 1, "/images/news_dunhuang.png",
     "莫高窟壁画保存了大量供养人形象，是研究历代服饰的第一手图像史料。第130窟《都督夫人礼佛图》中，盛装贵妇着红底花裙、披浅蓝披帛，身后侍女队列衣色纷呈，直观呈现唐代女子襦裙装束与丰腴雍容的时代审美。\n"
     "五代第98窟回鹘公主供养像身着红色圆领拖裾长袍、颈佩层层璎珞，与《旧唐书》所载回纥公主“通裾大襦，皆茜色”相互印证。\n"
     "展览以数字化复原让壁画人物“走”出洞窟，大袖襦裙与圆领袍形制成为学界研究焦点。",
     ["隋唐时期服饰形制有什么典型特征？", "壁画供养人服饰与文献记载如何互证？", "如何区分正统大袖襦裙复原与现代影楼装？"]),
    ("定陵出土织金妆花缎研究新进展",
     "明定陵出土织金妆花缎龙袍完成显微分析；明代织造工艺水平获学界再确认；织物纹样数字化采集启动。",
     "考古学报", "明", "马面裙,妆花缎", 0, "/images/news_dingling.png",
     "明定陵出土的织金孔雀羽妆花纱龙袍，是明代织造工艺的巅峰之作。史料记载，仅一件龙袍即用捻金线4000米、片金线11300根，可谓“寸金换寸锦”。\n"
     "龙袍以孔雀羽线绣龙，历经数百年龙纹依旧清晰可见；妆花缎织造技艺集挖花、织金、妆彩于一体，代表明代丝织的最高水平。\n"
     "考古人员已对龙袍完成显微分析，织物纹样数字化采集同步启动，为明代织造工艺研究提供了新证据。",
     ["明代服饰形制有什么典型特征？", "明代织金工艺如何实现“寸金换寸锦”？", "如何区分正统妆花缎复原与现代影楼装？"]),
    ("宋代黄昇墓服饰研究：一棺看清南宋衣冠",
     "黄昇墓出土服饰超300件；褙子、霞帔等宋代典型服饰实物佐证；福州南宋丝织技术研究再深入。",
     "文物天地", "宋", "褙子", 0, "/images/news_huangsheng.png",
     "南宋黄昇墓位于福建福州，出土服饰超过300件，被称为“一棺看清南宋衣冠”。墓主黄昇年仅17岁，随葬品以衣冠服饰为主，是迄今发现宋代女性服饰最完整的实例。\n"
     "其中花罗绣彩花边单衣为国家一级文物，合领对襟、无纽扣或系带，衣面以四经绞罗织就，绣梅花、牡丹、芙蓉、山茶、荷花等纹样，镶边配色丰富，清新雅致。\n"
     "褙子、霞帔等宋代典型服饰实物，为研究南宋丝织技术与服饰制度提供了珍贵佐证。",
     ["宋代服饰形制有什么典型特征？", "黄昇墓出土服饰为何被称为“一棺看清南宋衣冠”？", "如何区分正统褙子复原与现代影楼装？"]),
    ("明代马面裙再受关注：宜昌明墓出土实物展现裙式考究",
     "宜昌东山明墓出土马面裙完成整理；两侧打褶前后裙门平整，明代女性裙式典型；织金妆花缎工艺实证文献记载。",
     "宜昌博物馆", "明", "马面裙,妆花缎", 0, "/images/news_manianqun.png",
     "马面裙是明代女性最具代表性的裙式之一，因裙门形似马面得名。1988年宜昌东山明墓出土的马面裙两侧打褶、前后裙门平整，是明代女性裙式的典型实证。\n"
     "山东博物馆藏明代服饰中亦见织金妆花缎马面裙，藏蓝缎面织金缠枝纹样，工艺考究。\n"
     "此类实物与《明宫史》等文献记载相互印证，为明代服饰制度与染织工艺研究提供了珍贵材料。",
     ["明代服饰形制有什么典型特征？", "马面裙的褶裥与裙门有何形制规范？", "如何区分正统马面裙复原与现代影楼装？"]),
    ("秦陵铠甲武士俑服饰研究：甲片铆接再现秦军戎装",
     "秦始皇帝陵出土铠甲武士俑完成形制测绘；铆钉固定甲片、单板长冠标识军阶；秦代戎装体系研究获新进展。",
     "考古学报", "秦汉", "铠甲,武士俑", 0, "/images/news_bingmayong.png",
     "秦始皇陵兵马俑是中国古代服饰与军戎装备研究的第一手实物资料。出土铠甲武士俑头戴单板长冠，是秦代中下级军吏的典型标识；身着结构严密的铠甲，甲片以铆钉固定，兼具防护性与实用性。\n"
     "跪射俑背部甲片拼接规整、铆钉凸起清晰，陶土质感与工艺细节为复原秦代甲胄提供了精确尺度。\n"
     "秦陵铠甲研究对理解战国至秦代服饰制度、军阶标识与加工工艺具有重要意义。",
     ["秦代军戎服饰有什么典型特征？", "如何从陶俑反推秦代甲胄制作工艺？", "兵马俑服饰如何体现秦代军阶制度？"]),
    ("国博唐代陶俑印证圆领袍：胡服改制的官服常制",
     "国家博物馆藏唐俑穿圆领袍展示官服常制；圆领袍源自胡服、经改制融入中原礼制；领口结构细节为复原提供依据。",
     "中国丝绸博物馆", "隋唐", "圆领袍,陶俑", 0, "/images/news_yuanlingpao.png",
     "圆领袍是唐代最具代表性的官服常制之一，源于胡服，经中原化改造后成为从官员到庶民皆可穿用的袍服。国家博物馆展出的唐代陶俑多着圆领袍，躬身交臂、拱手抱胸姿态各异，直观呈现其穿着状态。\n"
     "三彩釉陶胡人服牵马俑（唐开元十一年）领口结构细节清晰，为圆领袍领型复原提供了重要依据。\n"
     "唐代开放的时代特性给圆领袍以肥沃的发展土壤，其形制与织染工艺带有浓重的胡服元素。",
     ["隋唐时期官服形制有什么典型特征？", "圆领袍的领口结构如何复原？", "如何区分正统圆领袍复原与现代影楼装？"]),
    ("云锦九龙图亮相：1600年皇家御用织造的当代传承",
     "南京云锦九龙图展示皇家御用织造技艺；妆花工艺集挖花织金妆彩于一体；非遗传承推动传统织造当代活化。",
     "非遗资讯", "明", "云锦,妆花", 0, "/images/news_yunjin.png",
     "南京云锦是1600年皇家御用织造的集大成者，也是中国四大名锦之首、人类非物质文化遗产。九龙图以明黄为底，龙身金黑为主，缀以红云、火焰与海水江崖，纹样繁复精美。\n"
     "云锦妆花工艺集挖花、织金、妆彩于一体，一件龙袍即用捻金线4000米、片金线11300根，“寸金换寸锦”名副其实。\n"
     "如今云锦非遗传承人正以现代设计语言活化传统织造，让皇家御用技艺走入当代生活。",
     ["云锦妆花工艺有什么典型特征？", "云锦纹样的吉祥寓意有哪些？", "如何区分正统云锦复原与现代仿品？"]),
]


def init_demo_db() -> None:
    """创建表并写入种子（幂等：已存在则跳过）。"""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if db.query(ForumBoards).count() > 0:
            return
        for name, desc in BOARDS:
            db.add(ForumBoards(name=name, description=desc))
        for name, dynasty, loc, lat, lng, museum, desc in RELICS:
            db.add(Relics(name=name, dynasty=dynasty, location=loc, geo_lat=lat,
                          geo_lng=lng, museum=museum, description=desc))
        db.flush()
        for name, dynasty, cat, wearer, src, fab, pat, color, desc, relic_id in COSTUMES:
            db.add(Costumes(name=name, dynasty=dynasty, category=cat, wearer=wearer,
                            source_type=src, fabric=fab, pattern=pat, color=color,
                            description=desc, relic_id=relic_id))
        db.flush()
        for costume_id, rtype, value, ref in RELATIONS:
            db.add(CostumeRelations(costume_id=costume_id, relation_type=rtype,
                                    target_value=value, source_ref=ref))
        for cid, dynasty, name, pj, pc, ref in TEMPLATES:
            db.add(PatternTemplates(costume_id=cid, dynasty=dynasty, name=name,
                                    pattern_json=pj, param_constraints=pc, source_ref=ref))
        for dynasty, ctype, rj, ref in RULES:
            db.add(PatternConstraintRules(dynasty=dynasty, costume_type=ctype,
                                          rule_json=rj, reference_source=ref))
        for name, dynasty, meaning, ref in PATTERNS:
            db.add(Patterns(name=name, dynasty=dynasty, meaning=meaning, source_ref=ref))
        for title, summary, source, dtags, etags, focus, cover, content, aqs in NEWS:
            db.add(News(title=title, summary=summary, source=source,
                        dynasty_tags=dtags, entity_tags=etags, is_focus=focus,
                        cover_image=cover, content=content,
                        ai_questions=json.dumps(aqs, ensure_ascii=False)))
        demo_hash = hash_password("yisu2026")
        admin = Users(username="admin", email="admin@yisu.ai", password_hash=demo_hash, role="admin")
        demo = Users(username="demo", email="demo@yisu.ai", password_hash=demo_hash, role="user")
        db.add_all([admin, demo])
        db.flush()  # 拿到 admin.id / demo.id 供社区种子外键使用

        POSTS = [
            (1, admin.id, "褙子两侧开衩的考据：黄昇墓实物给了我们什么证据？",
             "整理黄昇墓出土褙子的开衩位置与长度数据，结合《舆服杂录》记载，讨论宋代褙子开衩的确切形制。",
             "宋", "7", False, 12, 6, 3, 8),
            (2, demo.id, "从《簪花仕女图》看唐代大袖衫的广袖比例",
             "对《簪花仕女图》中仕女大袖比例做数字化测量，还原唐代大袖衫袖宽与衣长的视觉关系，欢迎一起讨论。",
             "隋唐", "5", False, 8, 4, 1, 5),
            (3, demo.id, "明代马面裙褶裥数量考证：定陵实物的启示",
             "定陵出土马面裙的褶裥数量与工艺细节对明代裙式复原的参考意义。",
             "明", "9", True, 20, 9, 5, 12),
        ]
        for b, uid, t, c, dtag, cid, pin, lk, cc, rc, rp in POSTS:
            db.add(ForumPosts(board_id=b, user_id=uid, title=t, content=c,
                              dynasty_tags=dtag, costume_ids=cid, is_pinned=pin,
                              like_count=lk, collect_count=cc, reply_count=rc,
                              repost_count=rp))
        db.flush()

        q = Questions(user_id=demo.id, title="宋代褙子和唐代大袖衫在形制上有什么区别？",
                      content="想从剪裁、袖型、领型几个角度了解两者的差异。",
                      dynasty_tags="宋,隋唐",
                      ai_answer="据《中国历代服饰史》与出土实物：褙子为直领对襟、两侧开衩的长衣，袖型相对收束，宋人日常外穿；大袖衫为广袖、领口低敞的礼服类外衣，多用于唐代宫廷与宴乐场合，袖宽显著大于褙子。",
                      ai_source_ref="《中国历代服饰史》；黄昇墓出土实物；《簪花仕女图》")
        db.add(q)
        db.flush()

        db.add_all([
            Answers(question_id=q.id, user_id=admin.id, content="补充：褙子开衩位置在身侧缝，深度约及腰；唐代大袖衫的领口多为直领对襟或圆领，两者朝代审美差异明显。",
                    is_ai_answer=False, source_ref="黄昇墓出土报告", vote_count=5),
            Answers(question_id=q.id, user_id=demo.id, content="另可参考宋代《东京梦华录》中‘背子’的记载，注意宋代背子与唐代半臂的区分。",
                    is_ai_answer=False, source_ref="《东京梦华录》", vote_count=2),
        ])
        db.add(ForumReplies(post_id=1, user_id=demo.id, content="补充：黄昇墓出土褙子开衩至腰部，直领对襟，两侧开衩为宋代典型特征。",
                            like_count=3))
        db.commit()
    finally:
        db.close()
