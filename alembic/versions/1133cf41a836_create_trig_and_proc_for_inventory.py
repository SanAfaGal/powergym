"""Create triggers and procedures for inventory system

Revision ID: 1133cf41a836
Revises: ef92c616f2e5
Create Date: 2025-10-25 17:14:10.563907

"""
from alembic import op

revision = '1133cf41a836'
down_revision = '37a5aad6f8ec'
branch_labels = None
depends_on = '37a5aad6f8ec'


def upgrade() -> None:
    """Create all triggers and procedures"""

    # ============================================================
    # PROCEDURE 1: Update product stock on movement insert
    # ============================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_product_stock()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE products
            SET available_quantity = available_quantity + NEW.quantity
            WHERE id = NEW.product_id;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_update_stock_on_movement
        AFTER INSERT ON inventory_movements
        FOR EACH ROW
        EXECUTE FUNCTION update_product_stock();
    """)

    # ============================================================
    # PROCEDURE 2: Revert product stock on movement delete
    # ============================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION revert_product_stock()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE products
            SET available_quantity = available_quantity - OLD.quantity
            WHERE id = OLD.product_id;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_revert_stock_on_delete
        BEFORE DELETE ON inventory_movements
        FOR EACH ROW
        EXECUTE FUNCTION revert_product_stock();
    """)

    # ============================================================
    # PROCEDURE 3: Validate stock not negative
    # ============================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_stock_not_negative()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.available_quantity < 0 THEN
                RAISE EXCEPTION 'Stock no puede ser negativo para producto %', NEW.id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_validate_stock_not_negative
        BEFORE UPDATE ON products
        FOR EACH ROW
        EXECUTE FUNCTION validate_stock_not_negative();
    """)

    # ============================================================
    # PROCEDURE 4: Update stock status based on quantity
    # ============================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_stock_status()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.available_quantity = 0 THEN
                NEW.stock_status = 'STOCK_OUT'::stock_status_enum;
            ELSIF NEW.available_quantity <= NEW.min_stock THEN
                NEW.stock_status = 'LOW_STOCK'::stock_status_enum;
            ELSIF NEW.max_stock IS NOT NULL AND NEW.available_quantity > NEW.max_stock THEN
                NEW.stock_status = 'OVERSTOCK'::stock_status_enum;
            ELSE
                NEW.stock_status = 'NORMAL'::stock_status_enum;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_update_stock_status
        BEFORE UPDATE ON products
        FOR EACH ROW
        EXECUTE FUNCTION update_stock_status();
    """)

    # ============================================================
    # PROCEDURE 5: Auto-update product updated_at timestamp
    # ============================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_product_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_update_product_timestamp
        BEFORE UPDATE ON products
        FOR EACH ROW
        EXECUTE FUNCTION update_product_timestamp();
    """)


def downgrade() -> None:
    """Drop all triggers and procedures"""

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_update_stock_on_movement ON inventory_movements;")
    op.execute("DROP TRIGGER IF EXISTS trigger_revert_stock_on_delete ON inventory_movements;")
    op.execute("DROP TRIGGER IF EXISTS trigger_validate_stock_not_negative ON products;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_stock_status ON products;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_product_timestamp ON products;")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_product_stock();")
    op.execute("DROP FUNCTION IF EXISTS revert_product_stock();")
    op.execute("DROP FUNCTION IF EXISTS validate_stock_not_negative();")
    op.execute("DROP FUNCTION IF EXISTS update_stock_status();")
    op.execute("DROP FUNCTION IF EXISTS update_product_timestamp();")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS stock_status_enum;")
    op.execute("DROP TYPE IF EXISTS inventory_movement_enum;")
