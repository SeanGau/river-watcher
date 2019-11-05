SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `members`;
CREATE TABLE `members` (
	`id` int(11) NOT NULL AUTO_INCREMENT,
	`username` text NOT NULL,
	`email` text NOT NULL,
	`password` text NOT NULL,
	PRIMARY KEY (`id`) USING BTREE
)CHARACTER SET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `resetpws`;
CREATE TABLE `resetpws` (
	`id` int(11) NOT NULL AUTO_INCREMENT,
	`email` text NOT NULL,
	`token` text NOT NULL,
	`times` text NOT NULL,
	PRIMARY KEY (`id`) USING BTREE
)CHARACTER SET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `river_subscribe`;
CREATE TABLE `river_subscribe` (
	`id` int(11) NOT NULL AUTO_INCREMENT,
	`email` text NOT NULL,
	`riverid` text NOT NULL,
	PRIMARY KEY (`id`) USING BTREE
)CHARACTER SET=utf8 COLLATE=utf8_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;