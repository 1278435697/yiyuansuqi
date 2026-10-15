-- 衣溯AI · 服装面料版块种子数据（14 种历代面料，考据来源见 source_ref）
-- 用法：mysql -uroot -p yisu_ai < seed_fabrics.sql

CREATE TABLE IF NOT EXISTS fabrics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  category VARCHAR(30) DEFAULT '',
  raw_material VARCHAR(100) DEFAULT '',
  dynasty_peak VARCHAR(50) DEFAULT '',
  technique VARCHAR(200) DEFAULT '',
  description TEXT,
  image_url VARCHAR(255) DEFAULT '',
  source_ref VARCHAR(255) DEFAULT '',
  created_by INT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO fabrics (name, category, raw_material, dynasty_peak, technique, description, image_url, source_ref) VALUES
('麻布','植物纤维','大麻·苎麻','先秦—秦汉','绩麻成纱·平纹织造','麻是先秦平民最主要的衣料，织造粗疏而结实。《诗经》多咏麻织，长沙马王堆一号汉墓出土细麻布残片，经纬致密，反映汉代麻纺水平。','/images/fabrics/fabric_ma.jpg','马王堆一号汉墓出土报告'),
('葛布','植物纤维','葛藤纤维','上古—先秦','煮葛取丝·平纹织造','葛是华夏最古老的衣料之一。《诗经·周南》"葛之覃兮，施于中谷"即咏采葛织布。浙江钱山漾遗址出土葛布残片，距今约4200年，为迄今最早纺织品实物之一。','/images/fabrics/fabric_ge.jpg','《诗经》·钱山漾遗址考古报告'),
('绢','动物纤维·丝','桑蚕丝','先秦—汉','平纹素织','绢为平纹素织丝织物，是古代最基础的丝织品。战国楚墓、马王堆汉墓均大量出土绢地绣品，凤鸟纹绣绢䋺衣即以紫红绢为地刺绣，绢面细密光洁。','/images/relics/relic_xianqin_shenyi.png','湖北荆州马山一号楚墓'),
('纱','动物纤维·丝','桑蚕丝','秦汉','方孔纱·平纹疏织','纱为经纬稀疏、孔隙透明的丝织物。长沙马王堆一号汉墓出土素纱单衣仅重48克，薄如蝉翼，代表西汉缫丝织造巅峰，为中国首批禁止出境展览文物。','/images/relics/relic_han_susha.png','湖南博物院·马王堆汉墓'),
('罗','动物纤维·丝','桑蚕丝','汉—唐','绞经组织·四经绞罗','罗以绞经起孔，质地轻薄而坚韧。马王堆出土朱红菱纹罗丝绵袍、唐代四经绞罗等，均为罗织精品，孔眼规整、透气性好，为贵族夏服首选。','/images/relics/relic_han_quju.png','马王堆一号汉墓·湖南博物院'),
('绮','动物纤维·丝','桑蚕丝','先秦—汉','平纹起斜纹花','绮为平纹地上起斜纹花的丝织物。河南信阳长台关楚墓出土杯纹绮，湖北江陵马山楚墓亦有出土，花纹以杯纹、几何纹为主，是汉代重要提花丝织品。','/images/relics/relic_geo_xinyang_beiwenqi.png','信阳长台关楚墓考古报告'),
('锦','动物纤维·丝','桑蚕丝','先秦—唐','重经重纬·多彩提花','锦为多彩提花丝织物，"织采为文，其价如金"。战国楚墓织锦、汉"五星出东方利中国"锦、唐代联珠对马纹锦皆属名品，青海都兰热水墓群出土织锦印证丝路织造交流。','/images/relics/relic_geo_dulan_zhijin.png','青海都兰热水墓群·青海省博物馆'),
('缂丝','织造工艺','桑蚕丝','唐—宋—明','通经断纬·织彩纬','缂丝以通经断纬法织造，花纹如雕镂，故称"刻丝"。南宋缂丝《莲塘乳鸭图》为传世绝品，明代缂丝龙袍工艺登峰造极，故宫藏绿缂丝金银万字地蝠寿纹氅衣为代表。','/images/relics/relic_qing_changyi.png','故宫博物院藏'),
('绫','动物纤维·丝','桑蚕丝','唐—宋','斜纹地起花','绫为斜纹地上起花的丝织物，质地平滑光泽。唐代绫织兴盛，敦煌文书所见"绫"品种繁多；宋代绫用于书画装裱与官服，宋绫组织细密、花纹雅致。','/images/relics/relic_tang_yuanling.png','敦煌文书·两宋织造文献'),
('缎','动物纤维·丝','桑蚕丝','元—明','缎纹组织','缎以缎纹组织织造，表面平滑光亮如绸缎。明代缎织大盛，五枚缎、妆花缎并兴，明定陵出土织金妆花缎、孔府旧藏桃红纱地彩绣大袖衫等均为明代缎织名品。','/images/relics/relic_geo_dingling_zhuanghua.png','明定陵出土·中国大百科全书'),
('妆花缎','织造工艺','桑蚕丝·金银线','明','挖花妆彩·织金','妆花缎以挖梭妆彩织造，纹样色彩丰富，常织金线。明定陵出土织金妆花缎龙袍、孝靖皇后百子衣等，代表明代宫廷织造的最高水平。','/images/relics/relic_geo_dingling_zhuanghua.png','明定陵博物馆'),
('纳石失','织造工艺','桑蚕丝·片金','元','织金锦·金线织入','纳石失（织金锦）为元代贵族礼服专用料，以金线织入锦地，光彩夺目。内蒙古集宁路古城遗址出土龟甲地瓣窠对格力芬彩锦，是元代织金锦代表。','/images/relics/relic_geo_jininglu_zhijin.png','内蒙古集宁路古城遗址'),
('漳绒','织造工艺','桑蚕丝','明清','起绒组织·割绒','漳绒以起绒组织织造并割绒，绒面密实柔软，明清时盛产福建漳州、南京等地。清宫旧藏蓝色漳绒团八宝大襟马褂为实物代表，绒圈与割绒交互显花。','/images/fabrics/fabric_rong.jpg','故宫博物院藏'),
('棉布','植物纤维','棉花','宋元—明清','轧棉纺纱·平纹织造','棉纺织自宋元传入并普及，元代黄道婆革新纺织工具，使松江棉布"衣被天下"。明清棉布取代麻布成为大众主要衣料，故宫藏清宫棉袍绵衣为实物佐证。','/images/fabrics/fabric_mian.jpg','《南村辍耕录》·故宫博物院藏');
