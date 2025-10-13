<?php

if (!defined('WPINC')) {
    die;
}

class RoyalAuth_API {

    public function __construct() {
        add_action('rest_api_init', array($this, 'register_routes'));
    }

    public function register_routes() {
        register_rest_route('royalauth/v1', '/license/(?P<action>\w+)', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_license_request'),
            'permission_callback' => '__return_true',
        ));
    }

    public function handle_license_request($request) {
        $action = $request['action'];
        $params = $request->get_json_params();

        if (empty($params['api_key']) || empty($params['api_secret'])) {
            return new WP_Error('missing_credentials', 'Missing API key or secret.', array('status' => 400));
        }

        require_once ROYALAUTH_PLUGIN_DIR . 'includes/class-royalauth-db.php';
        $app = RoyalAuth_DB::get_application_by_key($params['api_key']);

        if (!$app || !wp_check_password($params['api_secret'], $app->api_secret)) {
            return new WP_Error('invalid_credentials', 'Invalid API key or secret.', array('status' => 403));
        }

        switch ($action) {
            case 'status':
                return $this->get_status($app);
            case 'activate':
                return $this->activate($app);
            case 'deactivate':
                return $this->deactivate($app);
            default:
                return new WP_Error('invalid_action', 'Invalid action.', array('status' => 400));
        }
    }

    private function get_status($app) {
        return new WP_REST_Response(array(
            'status' => $app->is_active ? 'active' : 'inactive',
        ), 200);
    }

    private function activate($app) {
        RoyalAuth_DB::toggle_application_status($app->id, 1);
        // Log the activation event
        RoyalAuth_DB::add_log_entry($app->id, 'activate', $_SERVER['REMOTE_ADDR'], $_SERVER['HTTP_USER_AGENT']);
        return new WP_REST_Response(array('status' => 'activated'), 200);
    }

    private function deactivate($app) {
        RoyalAuth_DB::toggle_application_status($app->id, 0);
        // Log the deactivation event
        RoyalAuth_DB::add_log_entry($app->id, 'deactivate', $_SERVER['REMOTE_ADDR'], $_SERVER['HTTP_USER_AGENT']);
        return new WP_REST_Response(array('status' => 'deactivated'), 200);
    }
}

new RoyalAuth_API();