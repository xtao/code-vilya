#!/usr/bin/env python
# encoding: utf-8

# 
# ID: 5348d992__20140412_1413__snapshot
# timpstamp: 2014-04-12 14:13:38
# -------------------------------
# Snapshot: vilya
# 
# tables:
#   _yoyo_migration
#   card
#   cardlist
#   counter
#   permission
#   project
#   pull
#   team
#   user
# -------------------------------
#

from yoyo import step

step(
# forward action
"""

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `card`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `card` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `list_id` int(11) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` longtext,
  `number` int(11) NOT NULL,
  `order` int(11) NOT NULL,
  `is_archived` tinyint(1) NOT NULL,
  `archiver_id` int(11) NOT NULL,
  `closed_at` datetime DEFAULT NULL,
  `closer_id` int(11) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `card_closer_id` (`closer_id`),
  KEY `card_creator_id` (`creator_id`),
  KEY `card_archiver_id` (`archiver_id`),
  CONSTRAINT `card_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `user` (`id`),
  CONSTRAINT `card_ibfk_2` FOREIGN KEY (`archiver_id`) REFERENCES `user` (`id`),
  CONSTRAINT `card_ibfk_3` FOREIGN KEY (`closer_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `cardlist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cardlist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `creator_id` int(11) NOT NULL,
  `project_id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `number` int(11) NOT NULL,
  `order` int(11) NOT NULL,
  `role` int(11) NOT NULL,
  `is_archived` tinyint(1) DEFAULT NULL,
  `archiver_id` int(11) NOT NULL,
  `updated_at` datetime NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `cardlist_creator_id` (`creator_id`),
  KEY `cardlist_number` (`number`),
  KEY `cardlist_project_id` (`project_id`),
  KEY `cardlist_archiver_id` (`archiver_id`),
  KEY `cardlist_order` (`order`),
  CONSTRAINT `cardlist_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `user` (`id`),
  CONSTRAINT `cardlist_ibfk_2` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`),
  CONSTRAINT `cardlist_ibfk_3` FOREIGN KEY (`archiver_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `counter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `counter` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `count` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `perm_name` int(11) NOT NULL,
  `target_id` int(11) NOT NULL,
  `level` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `permission_user_id` (`user_id`),
  CONSTRAINT `permission_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `creator_id` int(11) NOT NULL,
  `ancestor_id` int(11) DEFAULT NULL,
  `owner_name` varchar(255) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `upstream` int(11) DEFAULT NULL,
  `counter_id` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `project_creator_id` (`creator_id`),
  KEY `project_counter_id` (`counter_id`),
  KEY `project_ancestor_id` (`ancestor_id`),
  CONSTRAINT `project_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `user` (`id`),
  CONSTRAINT `project_ibfk_2` FOREIGN KEY (`ancestor_id`) REFERENCES `project` (`id`),
  CONSTRAINT `project_ibfk_3` FOREIGN KEY (`counter_id`) REFERENCES `counter` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `pull`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pull` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `card_id` int(11) NOT NULL,
  `merged_at` datetime DEFAULT NULL,
  `merged_commit_sha` varchar(40) DEFAULT NULL,
  `origin_commit_sha` varchar(40) DEFAULT NULL,
  `origin_project` int(11) NOT NULL,
  `origin_project_ref` varchar(1024) NOT NULL,
  `upstream_commit_sha` varchar(40) DEFAULT NULL,
  `upstream_project` int(11) NOT NULL,
  `upstream_project_ref` varchar(1024) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `pull_card_id` (`card_id`),
  CONSTRAINT `pull_ibfk_1` FOREIGN KEY (`card_id`) REFERENCES `card` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `team`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `team` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(16) NOT NULL,
  `description` varchar(255) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `team_name` (`name`),
  KEY `team_creator_id` (`creator_id`),
  CONSTRAINT `team_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `active` tinyint(1) DEFAULT '0',
  `admin` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_username` (`username`),
  KEY `user_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;


""",

# rollback action
"""
DROP DATABASE vilya;
CREATE DATABASE vilya;
USE vilya;

CREATE TABLE `_yoyo_migration` (
  `id` varchar(255) NOT NULL,
  `ctime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


"""
)
