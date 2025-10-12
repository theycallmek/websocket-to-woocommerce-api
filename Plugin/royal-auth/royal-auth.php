<?php
/**
 * Plugin Name: RoyalAuth
 * Plugin URI: https://example.com/
 * Description: A WordPress plugin to manage authentication and provide a public API for license validation.
 * Version: 1.0.0
 * Author: Your Name
 * Author URI: https://example.com/
 * License: GPL2
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: royal-auth
 * Domain Path: /languages
 */

if (!defined('WPINC')) {
    die;
}

define('ROYALAUTH_VERSION', '1.0.0');
define('ROYALAUTH_PLUGIN_DIR', plugin_dir_path(__FILE__));

require_once ROYALAUTH_PLUGIN_DIR . 'includes/activation.php';
require_once ROYALAUTH_PLUGIN_DIR . 'includes/deactivation.php';

register_activation_hook(__FILE__, 'royalauth_activate');
register_deactivation_hook(__FILE__, 'royalauth_deactivate');

function royalauth_run() {
    require_once ROYALAUTH_PLUGIN_DIR . 'admin/class-royalauth-admin.php';
    new RoyalAuth_Admin();

    require_once ROYALAUTH_PLUGIN_DIR . 'includes/class-royalauth-api.php';
    new RoyalAuth_API();
}

add_action('plugins_loaded', 'royalauth_run');