CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    firstName VARCHAR(100),
    lastName VARCHAR(100),
    birthDate DATE,
    homeTown VARCHAR(100),
    homeTownState VARCHAR(100),
    hometownCountry   VARCHAR(100),
    currentCity VARCHAR(100),
    currentState VARCHAR(100),
    currentCountry VARCHAR(100),

    password varchar(255) NOT NULL,
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Friends(
  user_id1 INTEGER,
  user_id2 INTEGER,
  PRIMARY KEY (user_id1, user_id2),
  FOREIGN KEY (user_id1)
  REFERENCES Users(user_id),
  FOREIGN KEY (user_id2)
  REFERENCES Users(user_id)
);





CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);
CREATE TABLE Albums(
  albums_id INTEGER AUTO_INCREMENT,
  name VARCHAR(100),
  date DATE,
  user_id INTEGER NOT NULL,
  PRIMARY KEY (albums_id),
  FOREIGN KEY (user_id)
  REFERENCES Users(user_id)
);
CREATE TABLE Tags(
  tag_id INTEGER AUTO_INCREMENT,
  name VARCHAR(100),
  PRIMARY KEY (tag_id)
);

CREATE TABLE Tagged(
  photo_id INTEGER,
  tag_id INTEGER,
  PRIMARY KEY (photo_id, tag_id),
  FOREIGN KEY(photo_id)
  REFERENCES Photos (photo_id) ON DELETE CASCADE,
  FOREIGN KEY(tag_id)
  REFERENCES Tags (tag_id)
);
CREATE TABLE Comments(
  comment_id INTEGER AUTO_INCREMENT,
  comment VARCHAR(100),
  photo_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  PRIMARY KEY (comment_id),
  FOREIGN KEY (photo_id) REFERENCES Photos (photo_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users (user_id)
);

CREATE TABLE Likes(
  like_id INTEGER AUTO_INCREMENT,
  photo_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  PRIMARY KEY (like_id),
  FOREIGN KEY (photo_id) REFERENCES Photos (photo_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users (user_id)
);

INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
