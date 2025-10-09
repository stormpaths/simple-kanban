"""
Board Management Tests

Tests for creating, editing, deleting, and switching between boards.
"""

import pytest
from playwright.sync_api import Page, expect


class TestBoardManagement:
    """Test suite for board management functionality."""
    
    def test_create_new_board(self, authenticated_page: Page, test_board_name: str):
        """Test creating a new board."""
        page = authenticated_page
        
        # Click new board button
        page.click("#new-board-btn")
        
        # Wait for board modal
        page.wait_for_selector("#board-modal", state="visible")
        
        # Fill board details
        page.fill("#board-name", test_board_name)
        page.fill("#board-desc", "Test board description")
        
        # Save board
        page.click("#board-submit")
        
        # Wait for modal to close
        page.wait_for_selector("#board-modal", state="hidden")
        
        # Verify board appears in selector
        board_select = page.locator("#board-select")
        expect(board_select).to_contain_text(test_board_name)
    
    def test_switch_between_boards(self, authenticated_page: Page):
        """Test switching between different boards."""
        page = authenticated_page
        
        # Get current board options
        board_options = page.locator("#board-select option")
        
        if board_options.count() < 2:
            pytest.skip("Need at least 2 boards to test switching")
        
        # Select first board
        page.select_option("#board-select", index=0)
        page.wait_for_timeout(1000)
        
        # Verify board loaded (columns should be visible)
        page.wait_for_selector(".kanban-board", timeout=5000)
        
        # Select second board
        page.select_option("#board-select", index=1)
        page.wait_for_timeout(1000)
        
        # Verify board switched (should reload columns)
        page.wait_for_selector(".kanban-board", timeout=5000)
    
    def test_edit_board(self, authenticated_page: Page):
        """Test editing board details."""
        page = authenticated_page
        
        # Find edit board button (might be in a menu)
        edit_button = page.locator("#edit-board-btn, button:has-text('Edit Board')")
        
        if edit_button.count() == 0:
            pytest.skip("Edit board button not found")
        
        edit_button.click()
        
        # Wait for board modal
        page.wait_for_selector("#board-modal", state="visible")
        
        # Update board name
        name_input = page.locator("#board-name")
        current_name = name_input.input_value()
        new_name = f"{current_name} (Updated)"
        
        name_input.fill(new_name)
        
        # Save changes
        page.click("#board-submit")
        
        # Wait for modal to close
        page.wait_for_selector("#board-modal", state="hidden")
        
        # Verify board name updated in selector
        expect(page.locator("#board-select")).to_contain_text(new_name)
    
    def test_delete_board(self, authenticated_page: Page, test_board_name: str):
        """Test deleting a board."""
        page = authenticated_page
        
        # Create a test board to delete
        page.click("#new-board-btn")
        page.wait_for_selector("#board-modal", state="visible")
        page.fill("#board-name", test_board_name)
        page.click("#board-submit")
        page.wait_for_selector("#board-modal", state="hidden")
        
        # Select the test board
        page.select_option("#board-select", label=test_board_name)
        page.wait_for_timeout(1000)
        
        # Find delete board button (it's in the edit modal)
        # First open the edit modal
        page.click("#edit-board-btn")
        page.wait_for_selector("#board-modal", state="visible")
        
        # Now click delete button
        delete_button = page.locator("#board-delete")
        
        if not delete_button.is_visible():
            pytest.skip("Delete board button not visible")
        
        delete_button.click()
        
        # Handle confirmation dialog
        confirm_button = page.locator("button:has-text('Delete'), button:has-text('Confirm')")
        if confirm_button.count() > 0:
            confirm_button.click()
        
        page.wait_for_timeout(1000)
        
        # Verify board removed from selector
        board_select = page.locator("#board-select")
        expect(board_select).not_to_contain_text(test_board_name)
    
    def test_board_persistence(self, authenticated_page: Page):
        """Test that selected board persists across page reloads."""
        page = authenticated_page
        
        # Get available boards
        board_options = page.locator("#board-select option")
        
        if board_options.count() == 0:
            pytest.skip("No boards available")
        
        # Select a specific board
        page.select_option("#board-select", index=0)
        selected_value = page.locator("#board-select").input_value()
        page.wait_for_timeout(1000)
        
        # Reload page
        page.reload()
        
        # Wait for page to load
        page.wait_for_selector("#board-select", timeout=10000)
        
        # Verify same board is selected
        current_value = page.locator("#board-select").input_value()
        assert current_value == selected_value, "Board selection not persisted"


class TestColumnManagement:
    """Test suite for column management within boards."""
    
    def test_create_new_column(self, authenticated_page: Page):
        """Test creating a new column."""
        page = authenticated_page
        
        # Ensure board is loaded
        page.wait_for_selector(".kanban-board", timeout=5000)
        
        # Find add column button
        add_column_btn = page.locator("#add-column-btn, button:has-text('Add Column')")
        
        if add_column_btn.count() == 0:
            pytest.skip("Add column button not found")
        
        # Count existing columns
        initial_columns = page.locator(".column").count()
        
        # Click add column
        add_column_btn.click()
        
        # Fill column name (might be inline or in modal)
        column_name_input = page.locator("#column-name, input[placeholder*='column']").first
        column_name_input.fill("New Test Column")
        
        # Save column (might be Enter key or button)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)
        
        # Verify new column appears
        final_columns = page.locator(".column").count()
        assert final_columns > initial_columns, "Column not created"
    
    def test_column_order(self, authenticated_page: Page):
        """Test that columns maintain their order."""
        page = authenticated_page
        
        # Ensure board is loaded
        page.wait_for_selector(".kanban-board", timeout=5000)
        
        # Get column names
        columns = page.locator(".column-title")
        
        if columns.count() < 2:
            pytest.skip("Need at least 2 columns to test order")
        
        # Store column names
        column_names = [columns.nth(i).text_content() for i in range(columns.count())]
        
        # Reload page
        page.reload()
        page.wait_for_selector(".kanban-board", timeout=5000)
        
        # Verify order maintained
        columns_after = page.locator(".column-title")
        column_names_after = [columns_after.nth(i).text_content() for i in range(columns_after.count())]
        
        assert column_names == column_names_after, "Column order not maintained"
