<?php

if (!defined('WPINC')) {
    die;
}

class RoyalAuth_DB {

    /**
     * Get all applications from the database.
     */
    public static function get_applications() {
        global $wpdb;
        $table_name = $wpdb->prefix . 'royalauth_applications';
        return $wpdb->get_results("SELECT * FROM {$table_name} ORDER BY created_at DESC");
    }

    /**
     * Get all authentication logs from the database.
     */
    public static function get_auth_logs($limit = 20) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'royalauth_auth_logs';
        $apps_table_name = $wpdb->prefix . 'royalauth_applications';

        return $wpdb->get_results($wpdb->prepare(
            "SELECT l.*, a.name as app_name FROM {$table_name} l
             LEFT JOIN {$apps_table_name} a ON l.application_id = a.id
             ORDER BY l.timestamp DESC LIMIT %d",
            $limit
        ));
    }

    /**
     * Get the 'at a glance' metrics.
     */
    public static function get_metrics() {
        global $wpdb;
        $apps_table = $wpdb->prefix . 'royalauth_applications';
        $logs_table = $wpdb->prefix . 'royalauth_auth_logs';

        $total_apps = $wpdb->get_var("SELECT COUNT(*) FROM {$apps_table}");
        $active_keys = $wpdb->get_var("SELECT COUNT(*) FROM {$apps_table} WHERE is_active = 1");
        $activity_24h = $wpdb->get_var($wpdb->prepare(
            "SELECT COUNT(*) FROM {$logs_table} WHERE timestamp >= %s",
            date('Y-m-d H:i:s', strtotime('-24 hours'))
        ));

        return [
            'total_apps' => $total_apps,
            'active_keys' => $active_keys,
            'activity_24h' => $activity_24h,
        ];
    }

    /**
     * Toggle the status of an application.
     */
    public static function toggle_application_status($app_id, $is_active) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'royalauth_applications';

        return $wpdb->update(
            $table_name,
            ['is_active' => $is_active],
            ['id' => $app_id],
            ['%d'],
            ['%d']
        );
    }

    /**
     * Get an application by its API key.
     */
    public static function get_application_by_key($api_key) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'royalauth_applications';

        return $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$table_name} WHERE api_key = %s",
            $api_key
        ));
    }

    /**
     * Add a log entry.
     */
    public static function add_log_entry($app_id, $event_type, $ip_address, $user_agent) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'royalauth_auth_logs';

        $wpdb->insert(
            $table_name,
            [
                'application_id' => $app_id,
                'event_type' => $event_type,
                'ip_address' => $ip_address,
                'user_agent' => $user_agent,
            ],
            ['%d', '%s', '%s', '%s']
        );
    }
}