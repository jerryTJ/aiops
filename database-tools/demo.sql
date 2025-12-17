-- -------------------------------------------------------------
-- TablePlus 6.4.8(608)
--
-- https://tableplus.com/
--
-- Database: food
-- Generation Time: 2025-08-23 22:54:16.7270
-- -------------------------------------------------------------


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


DROP TABLE IF EXISTS `daily_macronutrients`;
CREATE TABLE `daily_macronutrients` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_name` varchar(50) DEFAULT NULL,
  `energy_kcal` varchar(50) DEFAULT NULL,
  `protein_g` varchar(50) DEFAULT NULL,
  `fat_g` varchar(50) DEFAULT NULL,
  `carbs_g` varchar(50) DEFAULT NULL,
  `fiber_g` varchar(50) DEFAULT NULL,
  `water_ml` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `daily_minerals`;
CREATE TABLE `daily_minerals` (
  `id` int NOT NULL AUTO_INCREMENT,
  `mineral_name` varchar(50) DEFAULT NULL,
  `unit` varchar(10) DEFAULT NULL,
  `male` varchar(50) DEFAULT NULL,
  `female` varchar(50) DEFAULT NULL,
  `child` varchar(50) DEFAULT NULL,
  `elderly` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `daily_vitamins`;
CREATE TABLE `daily_vitamins` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vitamin_name` varchar(50) DEFAULT NULL,
  `unit` varchar(10) DEFAULT NULL,
  `male` varchar(50) DEFAULT NULL,
  `female` varchar(50) DEFAULT NULL,
  `child` varchar(50) DEFAULT NULL,
  `elderly` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `food`;
CREATE TABLE `food` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `image_url` varchar(100) DEFAULT NULL,
  `vendor` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `food_ingredient`;
CREATE TABLE `food_ingredient` (
  `id` int NOT NULL AUTO_INCREMENT,
  `food_id` int DEFAULT NULL,
  `nutrition_id` int DEFAULT NULL,
  `weight` double NOT NULL DEFAULT '100' COMMENT '组合食物，各种材料的占比',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `food_nutrition`;
CREATE TABLE `food_nutrition` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(100) DEFAULT NULL COMMENT '商品名称',
  `unit` char(2) DEFAULT NULL COMMENT '单位（克）',
  `weight` int NOT NULL DEFAULT '100' COMMENT '默认100克',
  `energy` int DEFAULT NULL COMMENT '能量摄入（千卡）',
  `protein` int DEFAULT NULL COMMENT '蛋白质（克）',
  `fat` int DEFAULT NULL COMMENT '脂肪（克）',
  `carbohydrate` int DEFAULT NULL COMMENT '碳水化合物（克）',
  `dietaryFiber` int DEFAULT NULL COMMENT '膳食纤维（克）',
  `water` int DEFAULT NULL COMMENT '水（毫升）',
  `vitaminA` int DEFAULT NULL COMMENT '维生素A（微克）',
  `vitaminC` int DEFAULT NULL COMMENT '维生素C（毫克）',
  `vitaminD` int DEFAULT NULL COMMENT '维生素D（微克）',
  `vitaminE` int DEFAULT NULL COMMENT '维生素E（毫克）',
  `vitaminB1` int DEFAULT NULL COMMENT '维生素B1（毫克）',
  `vitaminB2` int DEFAULT NULL COMMENT '维生素B2（毫克）',
  `folicAcid` int DEFAULT NULL COMMENT '叶酸（微克）',
  `calcium` int DEFAULT NULL COMMENT '钙（毫克）',
  `iron` int DEFAULT NULL COMMENT '铁（毫克）',
  `zinc` int DEFAULT NULL COMMENT '锌（毫克）',
  `magnesium` int DEFAULT NULL COMMENT '镁（毫克）',
  `sodium` int DEFAULT NULL COMMENT '钠（毫克）',
  `potassium` int DEFAULT NULL COMMENT '钾（毫克）',
  `selenium` int DEFAULT NULL COMMENT '硒（微克）',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='食物营养推荐摄入量表（按人群）';

DROP TABLE IF EXISTS `receipt`;
CREATE TABLE `receipt` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '20250420',
  `receipt_url` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT 'origin receipt image',
  `created_data` datetime DEFAULT NULL,
  `vendor` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `shop_histories`;
CREATE TABLE `shop_histories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `weight` double NOT NULL DEFAULT '1',
  `cost` double DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  `food_name` varchar(100) DEFAULT NULL,
  `food_id` int DEFAULT NULL,
  `unit` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'pg',
  `receipt_id` int DEFAULT NULL,
  `image_url` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `mobile` varchar(100) DEFAULT NULL,
  `created_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `daily_macronutrients` (`id`, `group_name`, `energy_kcal`, `protein_g`, `fat_g`, `carbs_g`, `fiber_g`, `water_ml`) VALUES
(1, 'male', '2200–2600', '65–75', '60–80', '250–400', '25–30', '2000–2500'),
(2, 'female', '1800–2200', '55–65', '50–70', '220–350', '25–30', '1500–2000'),
(3, 'child', '1400–2200', '35–65', '40–70', '180–280', '10–15', '1200–1600'),
(4, 'older', '1600–2000', '65–75', '50–70', '200–300', '20–25', '1500–2000');

INSERT INTO `daily_minerals` (`id`, `mineral_name`, `unit`, `male`, `female`, `child`, `elderly`) VALUES
(1, '钙', 'mg', '800–1000', '800–1000', '800–1000', '1000–1200'),
(2, '铁', 'mg', '12', '20（育龄期）', '10–15', '12（女性略低）'),
(3, '锌', 'mg', '12.5', '7.5', '8–12', '12.5'),
(4, '镁', 'mg', '350–400', '300–350', '170–240', '350–400'),
(5, '钠', 'mg', '≤2000（盐5g）', '≤2000（盐5g）', '≤1200（盐3g）', '≤2000（盐5g）'),
(6, '钾', 'mg', '≥2000', '≥2000', '≥1500', '≥2000'),
(7, '硒', 'μg', '60', '50', '30–40', '60');

INSERT INTO `daily_vitamins` (`id`, `vitamin_name`, `unit`, `male`, `female`, `child`, `elderly`) VALUES
(1, '维生素A', 'μg', '800', '700', '500–700', '700–800'),
(2, '维生素C', 'mg', '100', '100', '60–90', '100–120'),
(3, '维生素D', 'μg', '10', '10', '10', '10–15'),
(4, '维生素E', 'mg', '14', '14', '7–10', '14'),
(5, '维生素B1', 'mg', '1.4', '1.2', '0.9–1.2', '1.2'),
(6, '维生素B2', 'mg', '1.4', '1.2', '1.0–1.4', '1.3'),
(7, '叶酸', 'μg', '400', '400-600', '200–300', '400');

INSERT INTO `food` (`id`, `name`, `image_url`, `vendor`) VALUES
(1, 'Croissant 10 Pack', 'http://image.foodai.com/a.png', 'WW'),
(2, 'Potato Wedges White Loose', 'http://image.foodai.com/a.png', 'WW'),
(3, 'HBS KSM NECTAR 2PKS', 'http://image.foodai.com/a.png', 'WW'),
(4, 'Value Pack Cookies Choc Chip 520g', 'http://image.foodai.com/a.png', 'WW'),
(5, 'M/Lean Fat Beef Mince 1kg\n', 'http://image.foodai.com/a.png', 'WW'),
(6, 'Lettuce Iceberg', 'http://image.foodai.com/a.png', 'WW');

INSERT INTO `food_ingredient` (`id`, `food_id`, `nutrition_id`, `weight`) VALUES
(1, 1, 1, 50),
(2, 1, 2, 50);

INSERT INTO `food_nutrition` (`id`, `name`, `unit`, `weight`, `energy`, `protein`, `fat`, `carbohydrate`, `dietaryFiber`, `water`, `vitaminA`, `vitaminC`, `vitaminD`, `vitaminE`, `vitaminB1`, `vitaminB2`, `folicAcid`, `calcium`, `iron`, `zinc`, `magnesium`, `sodium`, `potassium`, `selenium`) VALUES
(1, 'flour', 'G', 100, 100, 1, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(2, 'sugar', 'G', 100, 1000, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO `receipt` (`id`, `user_id`, `name`, `receipt_url`, `created_data`, `vendor`) VALUES
(1, 1, '20250515001', 'http://images.foodai.org.cn/a.png', '2025-05-15 15:21:25', 'WW');

INSERT INTO `shop_histories` (`id`, `weight`, `cost`, `created_date`, `food_name`, `food_id`, `unit`, `receipt_id`, `image_url`) VALUES
(1, 1, 10, '2025-05-15 15:23:55', 'Croissant 10 Pack', 1, 'pg', 1, 'http://images.foodai.org.cn/food.png'),
(2, 2, 9.7, '2025-05-15 15:27:28', 'HBS KSM NECTAR 2PKS', 3, 'pg', 1, 'http://images.foodai.org.cn/food.png'),
(3, 1.81, 3.31, '2025-05-15 15:28:05', 'Potato Wedges White Loose', 2, 'kg', 1, 'http://images.foodai.org.cn/food.png'),
(4, 1, 16.5, '2025-05-15 17:56:01', 'M/Lean Fat Beef Mince 1kg', 5, 'kg', 1, 'http://images.foodai.org.cn/food.png'),
(5, 1, 2.5, '2025-05-15 17:56:01', 'Lettuce Iceberg', 6, 'pg', NULL, NULL),
(6, 520, 2.5, '2025-05-15 17:56:01', 'Value Pack Cookies Choc Chip 520g', 4, 'pg', NULL, NULL);

INSERT INTO `users` (`id`, `name`, `mobile`, `created_date`) VALUES
(1, '20250515001', '18618102693', '2025-05-15 18:08:27');



/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;