<?php

if (!defined('WPINC')) {
    die;
}

/**
 * Creates the custom database tables on plugin activation.
 */
function royalauth_activate() {
    global $wpdb;
    require_once(ABSPATH . 'wp-admin/includes/upgrade.php');

    $charset_collate = $wpdb->get_charset_collate();

    // Table for applications
    $table_name_applications = $wpdb->prefix . 'royalauth_applications';
    $sql_applications = "CREATE TABLE {$table_name_applications} (
        id BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        api_key VARCHAR(255) NOT NULL,
        api_secret VARCHAR(255) NOT NULL,
        is_active TINYINT(1) NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY api_key (api_key)
    ) ENGINE=InnoDB {$charset_collate};";

    dbDelta($sql_applications);

    // Table for auth logs
    $table_name_logs = $wpdb->prefix . 'royalauth_auth_logs';
    $sql_logs = "CREATE TABLE {$table_name_logs} (
        id BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
        application_id BIGINT(20) UNSIGNED NOT NULL,
        event_type VARCHAR(50) NOT NULL,
        ip_address VARCHAR(100) NOT NULL,
        user_agent TEXT NOT NULL,
        timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        KEY application_id (application_id)
    ) ENGINE=InnoDB {$charset_collate};";

    dbDelta($sql_logs);
}