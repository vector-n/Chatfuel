-- Phase 3: Advanced Button Menus & Navigation
-- Migration: Enhanced menu system with multi-level support

-- Step 1: Add new columns to button_menus table
ALTER TABLE button_menus ADD COLUMN IF NOT EXISTS parent_menu_id BIGINT REFERENCES button_menus(id) ON DELETE SET NULL;
ALTER TABLE button_menus ADD COLUMN IF NOT EXISTS menu_type VARCHAR(20) DEFAULT 'static';  -- static, dynamic
ALTER TABLE button_menus ADD COLUMN IF NOT EXISTS data_source_config JSONB;  -- For dynamic menus
ALTER TABLE button_menus ADD COLUMN IF NOT EXISTS display_conditions JSONB;  -- Conditional display rules
ALTER TABLE button_menus ADD COLUMN IF NOT EXISTS is_default_menu BOOLEAN DEFAULT false;  -- Show on /start
ALTER TABLE button_menus ADD COLUMN IF NOT EXISTS menu_description TEXT;

-- Add index for parent_menu_id for faster hierarchy queries
CREATE INDEX IF NOT EXISTS idx_button_menus_parent_id ON button_menus(parent_menu_id);

-- Step 2: Create menu_buttons table (individual buttons in a menu)
CREATE TABLE IF NOT EXISTS menu_buttons (
    id BIGSERIAL PRIMARY KEY,
    menu_id BIGINT NOT NULL REFERENCES button_menus(id) ON DELETE CASCADE,
    
    -- Button display
    button_text VARCHAR(255) NOT NULL,
    emoji VARCHAR(10),
    row_position INTEGER DEFAULT 0,
    column_position INTEGER DEFAULT 0,
    
    -- Button type and action
    button_type VARCHAR(20) NOT NULL DEFAULT 'callback',  -- callback, url, webapp, contact, location
    action_type VARCHAR(50) NOT NULL,  -- message, submenu, broadcast, form, webhook, tag_user, etc.
    action_config JSONB NOT NULL DEFAULT '{}',  -- Flexible config for different actions
    
    -- Navigation targets
    target_menu_id BIGINT REFERENCES button_menus(id) ON DELETE SET NULL,  -- For submenu navigation
    target_form_id BIGINT REFERENCES forms(id) ON DELETE SET NULL,  -- For form launch (Phase 4)
    
    -- Conditional visibility
    requires_subscription BOOLEAN DEFAULT false,
    requires_tags VARCHAR(255)[],
    visible_to_premium_only BOOLEAN DEFAULT false,
    custom_visibility_rules JSONB,
    
    -- Order and state
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for menu_buttons
CREATE INDEX IF NOT EXISTS idx_menu_buttons_menu_id ON menu_buttons(menu_id);
CREATE INDEX IF NOT EXISTS idx_menu_buttons_target_menu ON menu_buttons(target_menu_id);
CREATE INDEX IF NOT EXISTS idx_menu_buttons_active ON menu_buttons(is_active);

-- Step 3: Menu navigation tracking (analytics)
CREATE TABLE IF NOT EXISTS menu_navigation_log (
    id BIGSERIAL PRIMARY KEY,
    bot_id BIGINT NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
    subscriber_id BIGINT NOT NULL REFERENCES subscribers(id) ON DELETE CASCADE,
    menu_id BIGINT REFERENCES button_menus(id) ON DELETE SET NULL,
    button_id BIGINT REFERENCES menu_buttons(id) ON DELETE SET NULL,
    
    action_taken VARCHAR(100),
    session_id VARCHAR(100),  -- Track navigation sessions
    
    navigated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for navigation log
CREATE INDEX IF NOT EXISTS idx_menu_nav_bot_id ON menu_navigation_log(bot_id);
CREATE INDEX IF NOT EXISTS idx_menu_nav_subscriber_id ON menu_navigation_log(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_menu_nav_date ON menu_navigation_log(navigated_at);

-- Step 4: Menu templates (pre-built menu structures)
CREATE TABLE IF NOT EXISTS menu_templates (
    id BIGSERIAL PRIMARY KEY,
    
    template_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),  -- e-commerce, education, support, service, etc.
    
    menu_structure JSONB NOT NULL,  -- Full menu tree structure
    preview_image_url TEXT,
    
    is_public BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for templates
CREATE INDEX IF NOT EXISTS idx_menu_templates_category ON menu_templates(category);
CREATE INDEX IF NOT EXISTS idx_menu_templates_public ON menu_templates(is_public);

-- Step 5: User's current menu context (track where user is in menu tree)
CREATE TABLE IF NOT EXISTS user_menu_context (
    id BIGSERIAL PRIMARY KEY,
    bot_id BIGINT NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
    subscriber_id BIGINT NOT NULL REFERENCES subscribers(id) ON DELETE CASCADE,
    
    current_menu_id BIGINT REFERENCES button_menus(id) ON DELETE SET NULL,
    menu_path BIGINT[],  -- Array of menu IDs showing navigation path
    session_id VARCHAR(100),
    
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_subscriber_bot_context UNIQUE (bot_id, subscriber_id)
);

-- Index for context
CREATE INDEX IF NOT EXISTS idx_user_menu_context_bot_subscriber ON user_menu_context(bot_id, subscriber_id);

-- Step 6: Auto-update triggers
CREATE OR REPLACE FUNCTION update_menu_buttons_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_menu_buttons_updated_at
    BEFORE UPDATE ON menu_buttons
    FOR EACH ROW
    EXECUTE FUNCTION update_menu_buttons_timestamp();

CREATE TRIGGER trigger_button_menus_updated_at
    BEFORE UPDATE ON button_menus
    FOR EACH ROW
    EXECUTE FUNCTION update_menu_buttons_timestamp();

-- Step 7: Migration of existing button_menus data (if any)
-- This preserves existing menus and creates corresponding menu_buttons

DO $$
DECLARE
    menu_record RECORD;
    button_record RECORD;
BEGIN
    -- Loop through existing menus that have button_data
    FOR menu_record IN 
        SELECT id, bot_id, button_data 
        FROM button_menus 
        WHERE button_data IS NOT NULL
    LOOP
        -- Check if button_data is an array
        IF jsonb_typeof(menu_record.button_data) = 'array' THEN
            -- Loop through each button in the array
            FOR button_record IN 
                SELECT 
                    value->>'text' as button_text,
                    value->>'callback_data' as callback_data,
                    (ROW_NUMBER() OVER () - 1) / 2 as row_pos,
                    (ROW_NUMBER() OVER () - 1) % 2 as col_pos
                FROM jsonb_array_elements(menu_record.button_data)
            LOOP
                -- Create menu_button entry
                INSERT INTO menu_buttons (
                    menu_id,
                    button_text,
                    row_position,
                    column_position,
                    button_type,
                    action_type,
                    action_config
                ) VALUES (
                    menu_record.id,
                    button_record.button_text,
                    button_record.row_pos,
                    button_record.col_pos,
                    'callback',
                    'message',  -- Default action
                    jsonb_build_object('callback_data', button_record.callback_data)
                );
            END LOOP;
        END IF;
    END LOOP;
END $$;

-- Step 8: Add helpful comments
COMMENT ON TABLE menu_buttons IS 'Individual buttons within a menu - Phase 3';
COMMENT ON TABLE menu_navigation_log IS 'Track user navigation through menus for analytics';
COMMENT ON TABLE menu_templates IS 'Pre-built menu templates that users can apply';
COMMENT ON TABLE user_menu_context IS 'Track current menu position for each user';
COMMENT ON COLUMN button_menus.parent_menu_id IS 'Parent menu ID for nested menus (NULL = root menu)';
COMMENT ON COLUMN button_menus.menu_type IS 'static = fixed buttons, dynamic = generated from data';
COMMENT ON COLUMN button_menus.is_default_menu IS 'Show this menu automatically on /start';

-- Complete!
SELECT 'Phase 3 migration completed successfully!' as status;
