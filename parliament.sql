PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE `users` (
	`id` INTEGER UNIQUE ON CONFLICT IGNORE NOT NULL,
	`screen_name` TEXT NOT NULL,
	`name` TEXT,
	`lang` TEXT NOT NULL DEFAULT `en`,
	`time_zone` TEXT NOT NULL DEFAULT `UTC`,
	`utc_offset` INTEGER NOT NULL DEFAULT `0`,
	`location` TEXT,
	`descr` TEXT,
	PRIMARY KEY(id)
);

CREATE TABLE `tweets` (
	`id`	INTEGER UNIQUE ON CONFLICT IGNORE NOT NULL,
	`timestamp`	INTEGER NOT NULL,
	`user_id`	INTEGER NOT NULL,
	`lang`	TEXT NOT NULL DEFAULT `en`,
	`location`	TEXT,
	`text`	TEXT NOT NULL,
	PRIMARY KEY(id)
);
CREATE UNIQUE INDEX `idx_unique_user` ON `users` (`id` ASC,`screen_name` ASC);
CREATE INDEX `idx_unique_tweet` ON `tweets` (`id` ASC);
CREATE INDEX `idx_tweets_by_user` ON `tweets` (`user_id` ASC);
COMMIT;
