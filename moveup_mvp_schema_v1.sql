
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    mobile VARCHAR(20) DEFAULT NULL,
    email VARCHAR(100) DEFAULT NULL,
    password_hash VARCHAR(255) DEFAULT NULL,
    nickname VARCHAR(50) NOT NULL,
    avatar_url VARCHAR(255) DEFAULT NULL,
    gender TINYINT DEFAULT 0 COMMENT '0未知 1男 2女',
    birthday DATE DEFAULT NULL,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 2禁言 3封禁 4注销',
    register_source VARCHAR(30) DEFAULT 'mobile' COMMENT 'mobile/wechat/email/admin',
    last_login_at DATETIME DEFAULT NULL,
    last_login_ip VARCHAR(64) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    UNIQUE KEY uk_mobile (mobile),
    UNIQUE KEY uk_email (email),
    KEY idx_status_created (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_profile (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    bio VARCHAR(255) DEFAULT NULL,
    height DECIMAL(5,2) DEFAULT NULL,
    weight DECIMAL(5,2) DEFAULT NULL,
    school_name VARCHAR(100) DEFAULT NULL,
    major_name VARCHAR(100) DEFAULT NULL,
    grade_name VARCHAR(50) DEFAULT NULL,
    fitness_goal VARCHAR(100) DEFAULT NULL COMMENT '减脂/增肌/养成习惯等',
    privacy_level TINYINT NOT NULL DEFAULT 1 COMMENT '1公开 2仅社群 3仅自己',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_login_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    login_type VARCHAR(30) NOT NULL COMMENT 'mobile/password/wechat/email/code',
    login_ip VARCHAR(64) DEFAULT NULL,
    device_id VARCHAR(128) DEFAULT NULL,
    user_agent VARCHAR(255) DEFAULT NULL,
    login_result TINYINT NOT NULL DEFAULT 1 COMMENT '1成功 2失败',
    fail_reason VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_user_created (user_id, created_at),
    KEY idx_device_created (device_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_ban_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    ban_type TINYINT NOT NULL COMMENT '1禁言 2封号',
    reason VARCHAR(255) NOT NULL,
    start_at DATETIME NOT NULL,
    end_at DATETIME DEFAULT NULL,
    operator_admin_id BIGINT DEFAULT NULL,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1生效中 2已解除 3已过期',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_user_status (user_id, status),
    KEY idx_start_end (start_at, end_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS community (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    cover_url VARCHAR(255) DEFAULT NULL,
    description VARCHAR(500) DEFAULT NULL,
    owner_user_id BIGINT NOT NULL,
    category VARCHAR(50) DEFAULT 'sport' COMMENT '跑步/健身/班级/校园等',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 2关闭 3冻结',
    member_count INT NOT NULL DEFAULT 0,
    post_count INT NOT NULL DEFAULT 0,
    is_public TINYINT NOT NULL DEFAULT 1 COMMENT '1公开 0私密',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    KEY idx_owner (owner_user_id),
    KEY idx_status_created (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS community_member (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    community_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    role TINYINT NOT NULL DEFAULT 1 COMMENT '1普通成员 2管理员 3群主',
    join_source VARCHAR(30) DEFAULT 'search',
    join_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 2退出 3被移除',
    mute_until DATETIME DEFAULT NULL,
    UNIQUE KEY uk_community_user (community_id, user_id),
    KEY idx_user_status (user_id, status),
    KEY idx_community_role (community_id, role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS community_notice (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    community_id BIGINT NOT NULL,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    publisher_user_id BIGINT NOT NULL,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1生效 0撤回',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_community_created (community_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS checkin_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    community_id BIGINT NOT NULL,
    sport_type VARCHAR(50) NOT NULL COMMENT 'run/walk/gym/cycle/swim/jump_rope/other',
    title VARCHAR(100) DEFAULT NULL,
    content VARCHAR(500) DEFAULT NULL,
    duration_minutes INT NOT NULL DEFAULT 0,
    distance_km DECIMAL(8,2) DEFAULT NULL,
    calories DECIMAL(8,2) DEFAULT NULL,
    checkin_date DATE NOT NULL COMMENT '打卡归属日期',
    start_time DATETIME DEFAULT NULL,
    end_time DATETIME DEFAULT NULL,
    source_type VARCHAR(30) DEFAULT 'manual' COMMENT 'manual/device/import',
    proof_status TINYINT NOT NULL DEFAULT 1 COMMENT '1无证明 2有截图 3有照片 4有视频',
    verify_status TINYINT NOT NULL DEFAULT 0 COMMENT '0待审 1自动通过 2人工待审 3通过 4驳回 5存疑',
    publish_status TINYINT NOT NULL DEFAULT 0 COMMENT '0草稿 1已发布 2隐藏 3删除',
    risk_score INT NOT NULL DEFAULT 0,
    like_count INT NOT NULL DEFAULT 0,
    comment_count INT NOT NULL DEFAULT 0,
    favorite_count INT NOT NULL DEFAULT 0,
    poster_url VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    KEY idx_user_date (user_id, checkin_date),
    KEY idx_community_date (community_id, checkin_date),
    KEY idx_publish_created (publish_status, created_at),
    KEY idx_verify_status (verify_status),
    KEY idx_sport_type (sport_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS checkin_media (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    checkin_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    media_type TINYINT NOT NULL COMMENT '1图片 2视频 3截图',
    media_url VARCHAR(255) NOT NULL,
    thumbnail_url VARCHAR(255) DEFAULT NULL,
    file_size BIGINT DEFAULT NULL,
    width INT DEFAULT NULL,
    height INT DEFAULT NULL,
    duration_seconds INT DEFAULT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    audit_status TINYINT NOT NULL DEFAULT 0 COMMENT '0待审 1通过 2驳回',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_checkin_sort (checkin_id, sort_order),
    KEY idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS checkin_poster (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    checkin_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    template_id VARCHAR(50) NOT NULL,
    poster_url VARCHAR(255) NOT NULL,
    poster_width INT DEFAULT NULL,
    poster_height INT DEFAULT NULL,
    generation_status TINYINT NOT NULL DEFAULT 1 COMMENT '1成功 2失败 3处理中',
    fail_reason VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_checkin_created (checkin_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS checkin_verify_result (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    checkin_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    ocr_text TEXT DEFAULT NULL,
    detected_app_name VARCHAR(100) DEFAULT NULL,
    detected_sport_type VARCHAR(50) DEFAULT NULL,
    detected_duration_minutes INT DEFAULT NULL,
    detected_distance_km DECIMAL(8,2) DEFAULT NULL,
    detected_calories DECIMAL(8,2) DEFAULT NULL,
    image_hash VARCHAR(128) DEFAULT NULL,
    similarity_score DECIMAL(5,2) DEFAULT NULL,
    risk_tags VARCHAR(255) DEFAULT NULL COMMENT '如duplicate,ocr_fail,edited',
    machine_result TINYINT NOT NULL DEFAULT 0 COMMENT '0待处理 1通过 2疑似异常 3失败',
    machine_score INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_checkin_id (checkin_id),
    KEY idx_machine_result (machine_result),
    KEY idx_image_hash (image_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS feed_post (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    community_id BIGINT NOT NULL,
    post_type TINYINT NOT NULL DEFAULT 1 COMMENT '1打卡动态 2普通发帖',
    related_checkin_id BIGINT DEFAULT NULL,
    title VARCHAR(100) DEFAULT NULL,
    content TEXT DEFAULT NULL,
    cover_url VARCHAR(255) DEFAULT NULL,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1展示 2隐藏 3删除',
    audit_status TINYINT NOT NULL DEFAULT 0 COMMENT '0待审 1通过 2驳回',
    visibility TINYINT NOT NULL DEFAULT 1 COMMENT '1公开 2仅社群 3仅自己',
    like_count INT NOT NULL DEFAULT 0,
    comment_count INT NOT NULL DEFAULT 0,
    favorite_count INT NOT NULL DEFAULT 0,
    view_count INT NOT NULL DEFAULT 0,
    hot_score DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_community_created (community_id, created_at),
    KEY idx_user_created (user_id, created_at),
    KEY idx_status_hot (status, hot_score),
    KEY idx_related_checkin (related_checkin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS post_like (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_post_user (post_id, user_id),
    KEY idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS post_comment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    parent_comment_id BIGINT DEFAULT NULL,
    reply_user_id BIGINT DEFAULT NULL,
    content VARCHAR(1000) NOT NULL,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 2隐藏 3删除',
    audit_status TINYINT NOT NULL DEFAULT 0 COMMENT '0待审 1通过 2驳回',
    like_count INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_post_created (post_id, created_at),
    KEY idx_user_created (user_id, created_at),
    KEY idx_parent (parent_comment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_room (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    community_id BIGINT NOT NULL,
    room_type TINYINT NOT NULL DEFAULT 1 COMMENT '1群聊 2私聊',
    name VARCHAR(100) DEFAULT NULL,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 2关闭',
    last_message_id BIGINT DEFAULT NULL,
    last_message_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_community_id (community_id),
    KEY idx_last_message_at (last_message_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_room_member (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    room_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    role TINYINT NOT NULL DEFAULT 1 COMMENT '1成员 2管理员',
    join_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mute_until DATETIME DEFAULT NULL,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 2退出 3移除',
    UNIQUE KEY uk_room_user (room_id, user_id),
    KEY idx_user_status (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_message (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    room_id BIGINT NOT NULL,
    sender_user_id BIGINT NOT NULL,
    message_type TINYINT NOT NULL COMMENT '1文本 2图片 3系统消息 4撤回消息',
    content TEXT DEFAULT NULL,
    media_url VARCHAR(255) DEFAULT NULL,
    reply_message_id BIGINT DEFAULT NULL,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 2撤回 3删除 4隐藏',
    audit_status TINYINT NOT NULL DEFAULT 0 COMMENT '0待审 1通过 2驳回',
    risk_score INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_room_created (room_id, created_at),
    KEY idx_sender_created (sender_user_id, created_at),
    KEY idx_reply_message (reply_message_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS content_report (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reporter_user_id BIGINT NOT NULL,
    target_type TINYINT NOT NULL COMMENT '1打卡 2动态 3评论 4聊天消息 5用户',
    target_id BIGINT NOT NULL,
    reason_type TINYINT NOT NULL COMMENT '1广告 2辱骂 3色情 4造假 5违法 6其他',
    reason_detail VARCHAR(500) DEFAULT NULL,
    status TINYINT NOT NULL DEFAULT 0 COMMENT '0待处理 1已处理 2已驳回',
    handler_admin_id BIGINT DEFAULT NULL,
    handle_result VARCHAR(255) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    handled_at DATETIME DEFAULT NULL,
    KEY idx_target (target_type, target_id),
    KEY idx_reporter_created (reporter_user_id, created_at),
    KEY idx_status_created (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_task (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_type TINYINT NOT NULL COMMENT '1打卡真实性 2动态内容 3评论内容 4聊天内容 5图片审核',
    target_type TINYINT NOT NULL COMMENT '1打卡 2动态 3评论 4聊天消息 5图片',
    target_id BIGINT NOT NULL,
    source VARCHAR(30) DEFAULT 'system' COMMENT 'system/report/manual',
    priority TINYINT NOT NULL DEFAULT 3 COMMENT '1高 2中 3低',
    risk_score INT NOT NULL DEFAULT 0,
    status TINYINT NOT NULL DEFAULT 0 COMMENT '0待处理 1处理中 2已完成 3关闭',
    assigned_admin_id BIGINT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_status_priority (status, priority),
    KEY idx_target (target_type, target_id),
    KEY idx_assigned_status (assigned_admin_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_result (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    audit_task_id BIGINT NOT NULL,
    target_type TINYINT NOT NULL,
    target_id BIGINT NOT NULL,
    reviewer_admin_id BIGINT NOT NULL,
    review_result TINYINT NOT NULL COMMENT '1通过 2驳回 3存疑 4封禁处理',
    review_reason VARCHAR(500) DEFAULT NULL,
    machine_assist_info TEXT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_task_id (audit_task_id),
    KEY idx_target (target_type, target_id),
    KEY idx_reviewer_created (reviewer_admin_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS risk_control_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT DEFAULT NULL,
    target_type TINYINT NOT NULL COMMENT '1登录 2打卡 3动态 4评论 5聊天',
    target_id BIGINT DEFAULT NULL,
    risk_type TINYINT NOT NULL COMMENT '1高频操作 2敏感词 3疑似造假 4重复内容 5设备异常',
    risk_level TINYINT NOT NULL COMMENT '1低 2中 3高',
    risk_detail VARCHAR(500) DEFAULT NULL,
    action_taken VARCHAR(100) DEFAULT NULL COMMENT 'pass/review/reject/mute/ban',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_user_created (user_id, created_at),
    KEY idx_target (target_type, target_id),
    KEY idx_risk_type_level (risk_type, risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_stats_daily (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    stat_date DATE NOT NULL,
    checkin_count INT NOT NULL DEFAULT 0,
    total_duration_minutes INT NOT NULL DEFAULT 0,
    total_distance_km DECIMAL(10,2) NOT NULL DEFAULT 0,
    total_calories DECIMAL(10,2) NOT NULL DEFAULT 0,
    post_count INT NOT NULL DEFAULT 0,
    comment_count INT NOT NULL DEFAULT 0,
    like_received_count INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_date (user_id, stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS community_stats_daily (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    community_id BIGINT NOT NULL,
    stat_date DATE NOT NULL,
    new_member_count INT NOT NULL DEFAULT 0,
    active_member_count INT NOT NULL DEFAULT 0,
    checkin_count INT NOT NULL DEFAULT 0,
    post_count INT NOT NULL DEFAULT 0,
    comment_count INT NOT NULL DEFAULT 0,
    message_count INT NOT NULL DEFAULT 0,
    report_count INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_community_date (community_id, stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS platform_stats_daily (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stat_date DATE NOT NULL,
    new_user_count INT NOT NULL DEFAULT 0,
    active_user_count INT NOT NULL DEFAULT 0,
    checkin_count INT NOT NULL DEFAULT 0,
    post_count INT NOT NULL DEFAULT 0,
    comment_count INT NOT NULL DEFAULT 0,
    message_count INT NOT NULL DEFAULT 0,
    report_count INT NOT NULL DEFAULT 0,
    audit_reject_count INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS admin_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(50) DEFAULT NULL,
    mobile VARCHAR(20) DEFAULT NULL,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1正常 2停用',
    last_login_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS admin_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL,
    role_code VARCHAR(50) NOT NULL,
    description VARCHAR(255) DEFAULT NULL,
    status TINYINT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_role_code (role_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS admin_permission (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    permission_name VARCHAR(100) NOT NULL,
    permission_code VARCHAR(100) NOT NULL,
    module_name VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_permission_code (permission_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS admin_role_permission (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    UNIQUE KEY uk_role_permission (role_id, permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS admin_user_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    admin_user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    UNIQUE KEY uk_admin_role (admin_user_id, role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
