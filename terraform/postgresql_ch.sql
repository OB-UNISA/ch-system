DROP TABLE IF EXISTS server CASCADE;
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
    ID       VARCHAR(100) PRIMARY KEY DEFAULT md5(random()::text),
    name     VARCHAR(30),
    serverID SMALLSERIAL,
    clanID   SERIAL,
    role     SMALLINT,
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
    userProfileID VARCHAR(100) PRIMARY KEY,
    key           VARCHAR(50) UNIQUE,
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS clanDiscord CASCADE;
CREATE TABLE clanDiscord
(
    clanID         SERIAL PRIMARY KEY,
    notifyWebhook  VARCHAR(1000),
    discordGuildID BIGINT UNIQUE,
    FOREIGN KEY (clanID)
        REFERENCES clan (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS timer CASCADE;
CREATE TABLE timer
(
    ID                 BIGSERIAL PRIMARY KEY,
    bossName           VARCHAR(50),
    type               VARCHAR(20),
    respawnTimeMinutes BIGINT NOT NULL,
    windowMinutes      BIGINT DEFAULT 0,
    timer              BIGINT,
    clanID             SERIAL,
    FOREIGN KEY (clanID)
        REFERENCES clan (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS discordID CASCADE;
CREATE TABLE discordID
(
    userProfileID VARCHAR(100) PRIMARY KEY,
    discordID     BIGINT UNIQUE,
    discordTag    VARCHAR(50),
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS webProfile CASCADE;
CREATE TABLE webProfile
(
    userProfileID VARCHAR(100) PRIMARY KEY,
    username      VARCHAR(50) UNIQUE,
    hash_pw       VARCHAR(150),
    change_pw     BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS webSession CASCADE;
CREATE TABLE webSession
(
    id            VARCHAR(200) UNIQUE,
    userProfileID VARCHAR(100),
    sessionID     VARCHAR(200) UNIQUE,
    host          VARCHAR(50),
    creation      timestamp DEFAULT now(),
    lastUse       timestamp DEFAULT now(),
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP TABLE IF EXISTS subscriber CASCADE;
CREATE TABLE subscriber
(
    userProfileID VARCHAR(100),
    timerID       BIGSERIAL,
    PRIMARY KEY (timerID, userProfileID),
    FOREIGN KEY (userProfileID)
        REFERENCES userProfile (ID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (timerID)
        REFERENCES timer (ID)
        ON UPDATE CASCADE ON DELETE CASCADE
);

DROP PROCEDURE IF EXISTS deleteOldSessions CASCADE;
CREATE PROCEDURE deleteOldSessions()
    LANGUAGE 'sql'
AS
$$
DELETE
FROM websession
WHERE creation < now() - interval '3 days'
   or creation = lastuse;
$$;
