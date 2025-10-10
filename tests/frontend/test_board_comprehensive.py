"""
Comprehensive Board Management Tests

This test suite validates that boards can be created, edited multiple times,
and all fields can be updated repeatedly without issues.
"""

import pytest
from playwright.sync_api import Page, expect


class TestBoardComprehensive:
    """Comprehensive test suite for board creation and editing."""

    def test_create_board_with_all_fields(self, authenticated_page: Page):
        """
        Test creating a board with all fields populated.

        Validates that both name and description are saved correctly.
        """
        page = authenticated_page

        # Click new board button
        page.click("#new-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        # Verify modal title
        expect(page.locator("#board-modal-title")).to_contain_text("Create New Board")

        # Fill all fields
        board_name = f"Complete Board {int(page.evaluate('Date.now()'))}"
        board_desc = "This is a comprehensive test board with full description"

        page.fill("#board-name", board_name)
        page.fill("#board-desc", board_desc)

        # Save board
        save_btn = page.locator("#board-submit")
        expect(save_btn).to_be_visible()
        expect(save_btn).to_be_enabled()
        save_btn.click()

        # Wait for modal to close
        page.wait_for_selector("#board-modal", state="hidden")
        page.wait_for_timeout(1000)

        # Verify board appears in selector
        board_select = page.locator("#board-select")
        expect(board_select).to_contain_text(board_name)

        # Select the board to verify it loads
        page.select_option("#board-select", label=board_name)
        page.wait_for_timeout(1000)

        # Verify board is displayed
        expect(page.locator("#board-title")).to_contain_text(board_name)
        expect(page.locator("#board-description")).to_contain_text(board_desc)

        print(f"✅ Board created with all fields: {board_name}")

    def test_edit_board_multiple_times_all_fields(self, authenticated_page: Page):
        """
        Test editing a board multiple times with all fields.

        This is the critical test for board modal reusability.
        """
        page = authenticated_page

        # Create a board first
        page.click("#new-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        initial_name = f"Multi-Edit Board {int(page.evaluate('Date.now()'))}"
        initial_desc = "Initial description"

        page.fill("#board-name", initial_name)
        page.fill("#board-desc", initial_desc)
        page.click("#board-submit")
        page.wait_for_selector("#board-modal", state="hidden")
        page.wait_for_timeout(1000)

        # Select the board
        page.select_option("#board-select", label=initial_name)
        page.wait_for_timeout(1000)

        # Now edit the board 3 times
        current_name = initial_name
        for iteration in range(3):
            print(f"\n=== Board Edit Iteration {iteration + 1} ===")

            # Click edit board button
            edit_btn = page.locator("#edit-board-btn")
            expect(edit_btn).to_be_visible()
            edit_btn.click()

            # Wait for modal
            page.wait_for_selector("#board-modal", state="visible")

            # Verify modal title changed to "Edit"
            expect(page.locator("#board-modal-title")).to_contain_text("Edit")

            # Verify current values are loaded
            name_input = page.locator("#board-name")
            desc_input = page.locator("#board-desc")

            expect(name_input).to_have_value(current_name)

            # Update both fields
            new_name = f"{initial_name} - Edit {iteration + 1}"
            new_desc = f"Updated description - iteration {iteration + 1}"

            name_input.fill(new_name)
            desc_input.fill(new_desc)

            # Verify submit button is enabled
            submit_btn = page.locator("#board-submit")
            expect(submit_btn).to_be_visible()
            expect(submit_btn).to_be_enabled()

            # Save changes
            submit_btn.click()

            # Wait for modal to close
            page.wait_for_selector("#board-modal", state="hidden")
            page.wait_for_timeout(1000)

            # Verify board name updated in selector
            expect(page.locator("#board-select")).to_contain_text(new_name)

            # Verify board name updated in display
            expect(page.locator("#board-title")).to_contain_text(new_name)
            expect(page.locator("#board-description")).to_contain_text(new_desc)

            # Update current name for next iteration
            current_name = new_name

            print(f"  ✅ Edit {iteration + 1} successful: {new_name}")

        print(f"\n✅ Successfully edited board 3 times - all fields working!")

        # Final verification - reopen and check data persisted
        edit_btn = page.locator("#edit-board-btn")
        edit_btn.click()
        page.wait_for_selector("#board-modal", state="visible")

        # Verify final values (should be iteration 3 - the last edit)
        expect(page.locator("#board-name")).to_have_value(current_name)
        expect(page.locator("#board-desc")).to_have_value(
            "Updated description - iteration 3"
        )

        print("✅ All changes persisted correctly!")

    def test_board_modal_cancel_button(self, authenticated_page: Page):
        """Test that cancel button works and doesn't save changes."""
        page = authenticated_page

        # Create a board
        page.click("#new-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        board_name = f"Cancel Test Board {int(page.evaluate('Date.now()'))}"
        page.fill("#board-name", board_name)
        page.fill("#board-desc", "Original description")
        page.click("#board-submit")
        page.wait_for_selector("#board-modal", state="hidden")
        page.wait_for_timeout(1000)

        # Select the board
        page.select_option("#board-select", label=board_name)
        page.wait_for_timeout(1000)

        # Open edit modal
        page.click("#edit-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        # Make changes
        page.fill("#board-name", "This should not be saved")
        page.fill("#board-desc", "This description should not be saved")

        # Click cancel
        cancel_btn = page.locator("#board-cancel")
        expect(cancel_btn).to_be_visible()
        cancel_btn.click()

        # Wait for modal to close
        page.wait_for_selector("#board-modal", state="hidden")
        page.wait_for_timeout(500)

        # Verify original name is still in selector
        expect(page.locator("#board-select")).to_contain_text(board_name)
        expect(page.locator("#board-select")).not_to_contain_text(
            "This should not be saved"
        )

        # Verify original data in display
        expect(page.locator("#board-title")).to_contain_text(board_name)
        expect(page.locator("#board-description")).to_contain_text(
            "Original description"
        )

        print("✅ Cancel button works - changes not saved")

    def test_board_modal_form_reset(self, authenticated_page: Page):
        """Test that board modal form resets between create operations."""
        page = authenticated_page

        # Open create modal and fill with data
        page.click("#new-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        page.fill("#board-name", "First Board Name")
        page.fill("#board-desc", "First Board Description")

        # Close without saving
        cancel_btn = page.locator("#board-cancel")
        cancel_btn.click()
        page.wait_for_selector("#board-modal", state="hidden")

        # Open create modal again
        page.click("#new-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        # Verify fields are empty
        expect(page.locator("#board-name")).to_have_value("")
        expect(page.locator("#board-desc")).to_have_value("")

        print("✅ Board modal form resets correctly")

    def test_rapid_board_modal_interactions(self, authenticated_page: Page):
        """Test rapid opening and closing of board modal."""
        page = authenticated_page

        # Rapidly open and close modal 5 times
        for i in range(5):
            page.click("#new-board-btn")
            page.wait_for_selector("#board-modal", state="visible", timeout=3000)

            # Immediately close
            page.click("#board-modal .modal-close")
            page.wait_for_selector("#board-modal", state="hidden", timeout=3000)

        # Verify modal still works normally
        page.click("#new-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        board_name = f"After Rapid Test {int(page.evaluate('Date.now()'))}"
        page.fill("#board-name", board_name)

        submit_btn = page.locator("#board-submit")
        expect(submit_btn).to_be_enabled()
        submit_btn.click()

        page.wait_for_selector("#board-modal", state="hidden")
        expect(page.locator("#board-select")).to_contain_text(board_name)

        print("✅ Board modal works after rapid interactions")

    def test_create_multiple_boards_sequentially(self, authenticated_page: Page):
        """Test creating multiple boards one after another."""
        page = authenticated_page

        board_names = []

        # Create 3 boards sequentially
        for i in range(3):
            page.click("#new-board-btn")
            page.wait_for_selector("#board-modal", state="visible")

            board_name = (
                f"Sequential Board {i + 1} - {int(page.evaluate('Date.now()'))}"
            )
            board_desc = f"Description for board {i + 1}"

            page.fill("#board-name", board_name)
            page.fill("#board-desc", board_desc)
            page.click("#board-submit")

            page.wait_for_selector("#board-modal", state="hidden")
            page.wait_for_timeout(1000)

            board_names.append(board_name)
            print(f"  ✅ Created board {i + 1}: {board_name}")

        # Verify all boards exist in selector
        board_select = page.locator("#board-select")
        for board_name in board_names:
            expect(board_select).to_contain_text(board_name)

        print(f"✅ Successfully created {len(board_names)} boards sequentially")


@pytest.mark.slow
class TestBoardEdgeCases:
    """Test edge cases for board management."""

    def test_board_name_validation(self, authenticated_page: Page):
        """Test that empty board name is not allowed."""
        page = authenticated_page

        page.click("#new-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        # Try to submit with empty name
        page.fill("#board-name", "")
        page.click("#board-submit")

        # Modal should stay open (validation failed)
        page.wait_for_timeout(500)

        # Modal should still be visible
        expect(page.locator("#board-modal")).to_be_visible()

        print("✅ Empty board name correctly rejected")

    def test_board_description_optional(self, authenticated_page: Page):
        """Test that board can be created without description."""
        page = authenticated_page

        page.click("#new-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        board_name = f"No Desc Board {int(page.evaluate('Date.now()'))}"

        # Fill only name, leave description empty
        page.fill("#board-name", board_name)
        page.fill("#board-desc", "")  # Explicitly empty

        page.click("#board-submit")
        page.wait_for_selector("#board-modal", state="hidden")

        # Verify board created
        expect(page.locator("#board-select")).to_contain_text(board_name)

        print("✅ Board created without description")

    def test_edit_board_persistence_after_reload(self, authenticated_page: Page):
        """Test that board edits persist after page reload."""
        page = authenticated_page

        # Create a board
        page.click("#new-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        original_name = f"Persistence Test {int(page.evaluate('Date.now()'))}"
        page.fill("#board-name", original_name)
        page.fill("#board-desc", "Original description")
        page.click("#board-submit")
        page.wait_for_selector("#board-modal", state="hidden")
        page.wait_for_timeout(1000)

        # Select the board
        page.select_option("#board-select", label=original_name)
        page.wait_for_timeout(1000)

        # Edit the board
        page.click("#edit-board-btn")
        page.wait_for_selector("#board-modal", state="visible")

        updated_name = f"{original_name} - Updated"
        updated_desc = "Updated description after reload test"

        page.fill("#board-name", updated_name)
        page.fill("#board-desc", updated_desc)
        page.click("#board-submit")
        page.wait_for_selector("#board-modal", state="hidden")
        page.wait_for_timeout(1000)

        # Reload page
        page.reload()
        page.wait_for_selector("#board-select", timeout=10000)

        # Verify updated board exists
        expect(page.locator("#board-select")).to_contain_text(updated_name)

        # Select it and verify description
        page.select_option("#board-select", label=updated_name)
        page.wait_for_timeout(1000)

        expect(page.locator("#board-title")).to_contain_text(updated_name)
        expect(page.locator("#board-description")).to_contain_text(updated_desc)

        print("✅ Board edits persisted after page reload")
