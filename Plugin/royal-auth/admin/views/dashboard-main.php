<div class="wrap">
    <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
    <p><?php _e('This dashboard provides an overview of your applications and their authentication activity.', 'royal-auth'); ?></p>

    <!-- At a Glance Stats -->
    <div id="dashboard-widgets-wrap">
        <div id="dashboard-widgets" class="metabox-holder">
            <div id="postbox-container-1" class="postbox-container">
                <div class="meta-box-sortables">
                    <div class="postbox">
                        <h2 class="hndle"><span><?php _e('At a Glance', 'royal-auth'); ?></span></h2>
                        <div class="inside">
                            <ul>
                                <li><strong><?php _e('Total Applications:', 'royal-auth'); ?></strong> <span id="total-apps"><?php echo esc_html($data['metrics']['total_apps']); ?></span></li>
                                <li><strong><?php _e('Active API Keys:', 'royal-auth'); ?></strong> <span id="active-keys"><?php echo esc_html($data['metrics']['active_keys']); ?></span></li>
                                <li><strong><?php _e('24-Hour Activity:', 'royal-auth'); ?></strong> <span id="24h-activity"><?php echo esc_html($data['metrics']['activity_24h']); ?></span></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Applications Table -->
    <h2><?php _e('Applications', 'royal-auth'); ?></h2>
    <table class="wp-list-table widefat fixed striped">
        <thead>
            <tr>
                <th scope="col" class="manage-column"><?php _e('Application Name', 'royal-auth'); ?></th>
                <th scope="col" class="manage-column"><?php _e('API Key', 'royal-auth'); ?></th>
                <th scope="col" class="manage-column"><?php _e('Status', 'royal-auth'); ?></th>
                <th scope="col" class="manage-column"><?php _e('Actions', 'royal-auth'); ?></th>
            </tr>
        </thead>
        <tbody id="the-list">
            <?php if (!empty($data['applications'])) : ?>
                <?php foreach ($data['applications'] as $app) : ?>
                    <tr>
                        <td><?php echo esc_html($app->name); ?></td>
                        <td><code><?php echo esc_html($app->api_key); ?></code></td>
                        <td><?php echo $app->is_active ? __('Active', 'royal-auth') : __('Inactive', 'royal-auth'); ?></td>
                        <td>
                            <form method="post" action="">
                                <input type="hidden" name="royalauth_action" value="toggle_status">
                                <input type="hidden" name="app_id" value="<?php echo esc_attr($app->id); ?>">
                                <input type="hidden" name="is_active" value="<?php echo $app->is_active ? 0 : 1; ?>">
                                <?php wp_nonce_field('royalauth_toggle_status', 'royalauth_nonce'); ?>
                                <button type="submit" class="button">
                                    <?php echo $app->is_active ? __('Deactivate', 'royal-auth') : __('Activate', 'royal-auth'); ?>
                                </button>
                            </form>
                        </td>
                    </tr>
                <?php endforeach; ?>
            <?php else : ?>
                <tr class="no-items"><td class="colspanchange" colspan="4"><?php _e('No applications found.', 'royal-auth'); ?></td></tr>
            <?php endif; ?>
        </tbody>
    </table>

    <!-- Activity Logs Table -->
    <h2 style="margin-top: 20px;"><?php _e('Recent Activity', 'royal-auth'); ?></h2>
    <table class="wp-list-table widefat fixed striped">
        <thead>
            <tr>
                <th scope="col" class="manage-column"><?php _e('Application', 'royal-auth'); ?></th>
                <th scope="col" class="manage-column"><?php _e('Event', 'royal-auth'); ?></th>
                <th scope="col" class="manage-column"><?php _e('IP Address', 'royal-auth'); ?></th>
                <th scope="col" class="manage-column"><?php _e('Timestamp', 'royal-auth'); ?></th>
            </tr>
        </thead>
        <tbody id="the-log-list">
            <?php if (!empty($data['logs'])) : ?>
                <?php foreach ($data['logs'] as $log) : ?>
                    <tr>
                        <td><?php echo esc_html($log->app_name); ?></td>
                        <td><?php echo esc_html($log->event_type); ?></td>
                        <td><?php echo esc_html($log->ip_address); ?></td>
                        <td><?php echo esc_html($log->timestamp); ?></td>
                    </tr>
                <?php endforeach; ?>
            <?php else : ?>
                <tr class="no-items"><td class="colspanchange" colspan="4"><?php _e('No recent activity.', 'royal-auth'); ?></td></tr>
            <?php endif; ?>
        </tbody>
    </table>
</div>