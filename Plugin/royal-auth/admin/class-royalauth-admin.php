<?php

if (!defined('WPINC')) {
    die;
}

class RoyalAuth_Admin {

    public function __construct() {
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_styles'));
        add_action('admin_init', array($this, 'handle_actions'));
    }

    public function handle_actions() {
        if (isset($_POST['royalauth_action']) && $_POST['royalauth_action'] === 'toggle_status') {
            if (!isset($_POST['royalauth_nonce']) || !wp_verify_nonce($_POST['royalauth_nonce'], 'royalauth_toggle_status')) {
                wp_die('Security check failed.');
            }

            $app_id = intval($_POST['app_id']);
            $is_active = intval($_POST['is_active']);

            require_once ROYALAUTH_PLUGIN_DIR . 'includes/class-royalauth-db.php';
            RoyalAuth_DB::toggle_application_status($app_id, $is_active);

            wp_redirect(admin_url('admin.php?page=royal-auth'));
            exit;
        }
    }

    public function enqueue_styles($hook) {
        // Only load on our plugin's admin page
        if ('toplevel_page_royal-auth' != $hook) {
            return;
        }
        wp_enqueue_style(
            'royalauth-admin-styles',
            plugin_dir_url(__FILE__) . 'assets/css/admin-styles.css',
            array(),
            ROYALAUTH_VERSION
        );
    }

    public function add_admin_menu() {
        add_menu_page(
            __('RoyalAuth', 'royal-auth'),
            __('RoyalAuth', 'royal-auth'),
            'manage_options',
            'royal-auth',
            array($this, 'render_dashboard_page'),
            'dashicons-shield-alt',
            25
        );
    }

    public function render_dashboard_page() {
        if (!current_user_can('manage_options')) {
            wp_die(__('You do not have sufficient permissions to access this page.'));
        }

        require_once ROYALAUTH_PLUGIN_DIR . 'includes/class-royalauth-db.php';

        $data = [
            'applications' => RoyalAuth_DB::get_applications(),
            'logs' => RoyalAuth_DB::get_auth_logs(),
            'metrics' => RoyalAuth_DB::get_metrics(),
        ];

        require_once ROYALAUTH_PLUGIN_DIR . 'admin/views/dashboard-main.php';
    }
}