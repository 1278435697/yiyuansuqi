-- 衣溯AI · 国风社区种子内容扩充（真实考据向帖子 + 回复）
-- 用法：mysql -uroot -p yisu_ai < seed_community_extra.sql

-- 形制溯源（board 1）补 3 帖
INSERT INTO forum_posts (board_id, user_id, title, content, dynasty_tags, like_count, reply_count, is_pinned, create_time) VALUES
(1, 1, '马王堆曲裾深衣的绕襟方向考：右衽还是左衽？', '关于汉代曲裾深衣的绕襟方向，马王堆一号汉墓出土的朱红菱纹罗丝绵袍为右衽绕襟，衣缘自右腋下向后缠绕。本文结合《礼记·深衣》"衽当旁"与出土实物照片，逐件核对曲裾的绕行方向与收掖位置，结论是汉代男女均以右衽为主，与先秦楚墓（如马山一号楚墓）一致。', '秦汉,深衣,马王堆', 18, 3, 1, DATE_SUB(NOW(), INTERVAL 5 DAY)),
(1, 1, '宋代褙子与明代比甲：直领对襟的千年流变', '褙子（直领对襟、两侧开衩）自五代出现，宋代成为士庶通用外衣；明代比甲无袖、对襟，二者形制同源但长度、袖型、系束方式各异。对比黄昇墓褙子（身长121cm）与定陵比甲实物数据，梳理"直领对襟"这一母题在宋明之间的演变。', '宋,明,褙子', 22, 2, 0, DATE_SUB(NOW(), INTERVAL 4 DAY)),
(1, 1, '深衣制度考：为什么说深衣"可以为文、可以为武"？', '《礼记·深衣》言深衣"可以为文，可以为武，可以傧相，可以治军旅"，其关键在于上衣下裳连属的结构兼具礼制与实用。本文从裁制（十二幅、续衽钩边）、衣长（短毋见肤、长毋被土）、用途三个维度展开，并对照长沙马王堆出土袍服的实测数据。', '先秦,深衣,礼制', 15, 1, 0, DATE_SUB(NOW(), INTERVAL 3 DAY));

-- 复原作品（board 2）补 3 帖
INSERT INTO forum_posts (board_id, user_id, title, content, dynasty_tags, like_count, reply_count, is_pinned, create_time) VALUES
(2, 1, '【复原】唐代圆领袍的纸样推导：从阿斯塔那实物到现代版型', '以吐鲁番阿斯塔那唐墓出土圆领袍实物为基础，推导唐代圆领袍的版型参数：领宽、衽斜、袖展、下摆。配合自制纸样图解，给出可用于现代制作的等比版型，欢迎同好讨论数据误差。', '隋唐,圆领袍,版型', 31, 4, 0, DATE_SUB(NOW(), INTERVAL 4 DAY)),
(2, 1, '【复原】明代马面裙：褶裥打版与裙门工艺详解', '基于定陵出土马面裙（褶裥数量与裙门宽度）与孔府旧藏实物，详解马面裙的打版流程：前后裙门、两侧褶裥、腰头系带。附自绘结构板片图与裁制参数表（裙长、腰围、褶宽），力求做到"每一条褶都有出处"。', '明,马面裙,打版', 27, 3, 0, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(2, 1, '【复原】魏晋大袖衫：从《洛神赋图》到成衣', '以《洛神赋图》《女史箴图》中魏晋名士宽衣博带之姿为图像依据，结合南北朝墓葬壁画，复原魏晋大袖衫：通袖长可达3米以上，袖口宽博，衣身随体。分享布料用量、放量计算与穿着层次（中衣+大袖衫+披帛）。', '魏晋,大袖衫,复原', 19, 2, 0, DATE_SUB(NOW(), INTERVAL 2 DAY));

-- 纹样文创（board 3）补 3 帖
INSERT INTO forum_posts (board_id, user_id, title, content, dynasty_tags, like_count, reply_count, is_pinned, create_time) VALUES
(3, 1, '宝相花的谱系：从忍冬纹到缠枝莲的千年演变', '宝相花是唐代最重要的装饰纹样，其来源可追溯至汉晋忍冬纹、莲花纹，并吸收佛教艺术元素。本文梳理宝相花从初唐到明清的形态演变（对称结构→多层宝相→缠枝化），附各时期文物纹样对比。', '纹样,宝相花,唐代', 24, 3, 0, DATE_SUB(NOW(), INTERVAL 5 DAY)),
(3, 1, '云气纹的宇宙观：汉锦上的"气象"叙事', '汉代织锦上的云气纹不仅是一种装饰，更承载"气化宇宙"的观念。马王堆、尼雅遗址出土汉锦中，云气纹与神兽、铭文（如"五星出东方利中国"）组合，构成汉代人想象的天界图景。', '纹样,汉锦,云气纹', 17, 2, 0, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(3, 1, '十二生肖纹在明清服饰中的用法：从肚兜到补子', '十二生肖纹样在明清服饰中多用于儿童肚兜、暖耳、荷包等小件，取"生肖护佑"之意；文官补子则用禽鸟、武官用猛兽，与生肖纹用途截然不同。本文以故宫藏品为例，区分两类纹样的礼制语境。', '明清,生肖纹,纹样', 13, 1, 0, DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 史料求助（board 4）补 3 帖
INSERT INTO forum_posts (board_id, user_id, title, content, dynasty_tags, like_count, reply_count, is_pinned, create_time) VALUES
(4, 1, '求教：宋代"翟衣"与明代"翟衣"的纹样差异？', '翟衣为后妃礼服。宋《政和五礼新仪》载翟衣织翟纹，明《大明会典》载皇后翟衣"织翟纹十有二等"。请问宋明两代翟衣的翟纹排列、底纹与边缘制度有何具体差异？求有考据的答复。', '宋,明,礼服', 9, 2, 0, DATE_SUB(NOW(), INTERVAL 4 DAY)),
(4, 1, '《舆服志》中"绛纱袍"与"绛纱单衣"的区别？', '检索历代舆服志，"绛纱袍"多次出现，又有"绛纱单衣"。二者是同一件衣物的不同称呼，还是形制有别的两类？具体到唐宋制度中如何区分？恳请史料达人解惑。', '舆服志,礼服', 7, 1, 0, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(4, 1, '请教：明代士人常服的"道袍"与"直裰"如何分辨？', '道袍与直裰皆为明代士人常服。有说法称道袍有内摆（暗摆）、直裰无摆，也有说法称直裰为道袍别称。请依据明代文献（《三才图会》《酌中志》等）与传世实物，给出可操作的辨识方法。', '明,道袍,直裰', 11, 3, 0, DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 给部分新帖补回复（作者名待前端联查，这里 user_id 用系统种子用户 1）
INSERT INTO forum_replies (post_id, user_id, content, parent_reply_id, like_count, create_time) VALUES
((SELECT id FROM forum_posts WHERE title LIKE '马王堆曲裾深衣%'), 1, '补充一个证据：马山一号楚墓N15袍亦为右衽，楚汉衣制一脉相承。', NULL, 3, DATE_SUB(NOW(), INTERVAL 4 DAY)),
((SELECT id FROM forum_posts WHERE title LIKE '马王堆曲裾深衣%'), 1, '请教：左衽是否只见于个别异俗或丧服记载？', NULL, 1, DATE_SUB(NOW(), INTERVAL 3 DAY)),
((SELECT id FROM forum_posts WHERE title LIKE '宋代褙子与明代比甲%'), 1, '补充黄昇墓褙子袖口数据：通袖长可达141cm，两袖端接缝位置与宋墓普遍一致。', NULL, 2, DATE_SUB(NOW(), INTERVAL 3 DAY)),
((SELECT id FROM forum_posts WHERE title LIKE '【复原】唐代圆领袍%'), 1, '请教袖展数据：阿斯塔那实物通袖长是多少？与纸样推算误差如何控制？', NULL, 1, DATE_SUB(NOW(), INTERVAL 3 DAY)),
((SELECT id FROM forum_posts WHERE title LIKE '【复原】明代马面裙%'), 1, '裙门宽建议按实物2:1复核，定陵马面裙前后裙门尺寸可查《定陵出土文物图典》。', NULL, 2, DATE_SUB(NOW(), INTERVAL 2 DAY)),
((SELECT id FROM forum_posts WHERE title LIKE '宝相花的谱系%'), 1, '补充：敦煌莫高窟331窟壁画中的宝相花可视为初唐标准型。', NULL, 1, DATE_SUB(NOW(), INTERVAL 4 DAY)),
((SELECT id FROM forum_posts WHERE title LIKE '请教：明代士人常服%'), 1, '《酌中志》明言"道袍，制如直裰"，但道袍有摆而直裰无摆之说多见于晚明笔记，可再考。', NULL, 2, DATE_SUB(NOW(), INTERVAL 1 DAY)),
((SELECT id FROM forum_posts WHERE title LIKE '求教：宋代"翟衣"%'), 1, '宋代翟衣翟纹九等（《政和五礼新仪》），明代定为十二等，纹样层级确有差异。', NULL, 2, DATE_SUB(NOW(), INTERVAL 3 DAY));

-- 同步板块帖子计数
UPDATE forum_boards b SET b.post_count = (SELECT COUNT(*) FROM forum_posts p WHERE p.board_id = b.id);
SELECT b.name, b.post_count FROM forum_boards b;
SELECT COUNT(*) total_posts FROM forum_posts;
