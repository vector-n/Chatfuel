-- Phase 3: Add Missing Columns to button_menus (SAFE)
-- This migration adds ONLY the columns that are missing
-- Safe to run even if some columns already exist

-- Add Phase 3 columns to button_menus table
DO $$ 
BEGIN
    -- Add menu_description if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'button_menus' AND column_name = 'menu_description'
    ) THEN
        ALTER TABLE button_menus ADD COLUMN menu_description TEXT;
    END IF;

    -- Add parent_menu_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'button_menus' AND column_name = 'parent_menu_id'
    ) THEN
        ALTER TABLE button_menus ADD COLUMN parent_menu_id BIGINT REFERENCES button_menus(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_button_menus_parent_id ON button_menus(parent_menu_id);
    END IF;

    -- Add menu_type if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'button_menus' AND column_name = 'menu_type'
    ) THEN
        ALTER TABLE button_menus ADD COLUMN menu_type VARCHAR(20) DEFAULT 'static';
    END IF;

    -- Add data_source_config if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'button_menus' AND column_name = 'data_source_config'
    ) THEN
        ALTER TABLE button_menus ADD COLUMN data_source_config JSONB;
    END IF;

    -- Add display_conditions if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'button_menus' AND column_name = 'display_conditions'
    ) THEN
        ALTER TABLE button_menus ADD COLUMN display_conditions JSONB;
    END IF;

    -- Add is_default_menu if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'button_menus' AND column_name = 'is_default_menu'
    ) THEN
        ALTER TABLE button_menus ADD COLUMN is_default_menu BOOLEAN DEFAULT false;
    END IF;

END $$;

-- Verify the columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'button_menus' 
AND column_name IN (
    'menu_description', 
    'parent_menu_id', 
    'menu_type', 
    'data_source_config', 
    'display_conditions', 
    'is_default_menu'
)
ORDER BY column_name;

-- Success message
SELECT '✅ Phase 3 columns added to button_menus table!' as status;
