DROP TABLE IF EXISTS server CASCADE ;
CREATE TABLE server
(
    ID   SMALLSERIAL PRIMARY KEY,
    name VARCHAR(20)
);

DROP TABLE IF EXISTS clan CASCADE;
CREATE TABLE clan
(
    ID       SERIAL PRIMARY KEY,
    name     VARCHAR(20),
    serverID SMALLSERIAL,
    FOREIGN KEY (serverID)
        REFERENCES server (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS userProfile CASCADE;
CREATE TABLE userProfile
(
    ID        SERIAL PRIMARY KEY,
    name      VARCHAR(30),
    serverID  SMALLSERIAL,
    clanID    SERIAL,
    role      SMALLINT,
    hash_pw   VARCHAR(150),
    change_pw BOOLEAN,
    FOREIGN KEY (clanID)
        REFERENCES clan (ID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (serverID)
        REFERENCES server (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS apiKey CASCADE;
CREATE TABLE apiKey
(
    userProfileID SERIAL PRIMARY KEY,
    key           VARCHAR(50) UNIQUE,
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS discordID CASCADE;
CREATE TABLE discordID
(
    userProfileID SERIAL PRIMARY KEY,
    discordID     VARCHAR(30),
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS timer CASCADE;
CREATE TABLE timer
(
    ID       SERIAL PRIMARY KEY,
    bossName VARCHAR(50),
    type     VARCHAR(20),
    timer    BIGINT,
    serverID SMALLSERIAL,
    clanID   SERIAL,
    FOREIGN KEY (clanID)
        REFERENCES clan (ID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (serverID)
        REFERENCES server (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS subscriber CASCADE;
CREATE TABLE subscriber
(
    userProfileID SERIAL,
    timerID       SERIAL,
    PRIMARY KEY (timerID, userProfileID),
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (timerID)
        REFERENCES timer (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);