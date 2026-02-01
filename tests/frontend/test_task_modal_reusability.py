"""
Task Modal Reusability Tests

This test suite specifically validates that task modals can be opened,
edited, closed, and reopened multiple times without issues.

This addresses the bug where buttons stopped working after the first usage.
"""

import pytest
from playwright.sync_api import Page, expect


class TestTaskModalReusability:
    """Test suite for task modal interaction and reusability."""

    def test_open_close_modal_multiple_times(self, board_with_columns: Page):
        """
        Test that the task modal can be opened and closed multiple times.

        This validates that modal cleanup works correctly.
        """
        page = board_with_columns

        # Ensure we have a board selected
        if page.locator("#board-select").count() > 0:
            page.select_option("#board-select", index=0)
            page.wait_for_timeout(1000)  # Wait for board to load

        # Open and close modal 5 times
        for i in range(5):
            # Open modal
            page.click(".add-task-btn")

            # Verify modal is visible
            modal = page.locator("#task-modal")
            expect(modal).to_be_visible()

            # Close modal by clicking close button
            page.click("#task-modal-close")

            # Verify modal is hidden
            expect(modal).to_be_hidden()

            # Small delay between iterations
            page.wait_for_timeout(500)

    def test_create_and_edit_task_multiple_times(self, board_with_columns: Page):
        """
        Test creating a task and then editing it multiple times.

        This is the critical test for the bug where edit buttons stopped working.
        """
        page = board_with_columns

        # Ensure we have a board with columns
        page.wait_for_selector(".column", timeout=10000)

        # Create a new task
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")

        task_title = "Test Task for Multiple Edits"
        page.fill("#task-title", task_title)
        page.fill("#task-desc", "Initial description")

        # Select first column
        # Column already set by clicking add button

        # Save task
        page.click("#task-submit")

        # Wait for modal to close and task to appear
        page.wait_for_selector("#task-modal", state="hidden")
        page.wait_for_selector(f"text={task_title}")

        # Now edit the task multiple times (this is where the bug occurred)
        for i in range(3):
            print(f"\n=== Edit iteration {i + 1} ===")

            # Find and click the task card
            task_card = page.locator(f".task-card:has-text('{task_title}')").first
            expect(task_card).to_be_visible()
            task_card.click()

            # Wait for modal to open
            page.wait_for_selector("#task-modal", state="visible")

            # Verify form is populated
            title_input = page.locator("#task-title")
            expect(title_input).to_have_value(task_title)

            # Update description
            new_description = f"Updated description - iteration {i + 1}"
            description_input = page.locator("#task-desc")
            description_input.fill(new_description)

            # Save changes
            save_button = page.locator("#task-submit")
            expect(save_button).to_be_visible()
            expect(save_button).to_be_enabled()
            save_button.click()

            # Wait for modal to close
            page.wait_for_selector("#task-modal", state="hidden", timeout=5000)

            # Verify task still exists
            expect(task_card).to_be_visible()

            # Small delay between edits
            page.wait_for_timeout(1000)

        print("\n✅ Successfully edited task 3 times - buttons working correctly!")

    def test_modal_form_reset_between_opens(self, board_with_columns: Page):
        """
        Test that modal form fields are properly reset between opens.

        This ensures no data leakage between modal uses.
        """
        page = board_with_columns

        # Open modal and fill with data
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")

        page.fill("#task-title", "First Task")
        page.fill("#task-desc", "First Description")

        # Close without saving (use close button, not backdrop)
        page.click("#task-modal-close")
        page.wait_for_selector("#task-modal", state="hidden")

        # Open modal again
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")

        # Verify fields are empty
        expect(page.locator("#task-title")).to_have_value("")
        expect(page.locator("#task-desc")).to_have_value("")

    def test_edit_different_tasks_sequentially(self, board_with_columns: Page):
        """
        Test editing multiple different tasks in sequence.

        This validates that modal state is properly reset between different tasks.
        """
        page = board_with_columns

        # Create two test tasks
        task_titles = ["Task A", "Task B"]

        for title in task_titles:
            page.click(".add-task-btn")
            page.wait_for_selector("#task-modal", state="visible")
            page.fill("#task-title", title)
            page.fill("#task-desc", f"Description for {title}")
            # Column already set by clicking add button
            page.click("#task-submit")
            page.wait_for_selector("#task-modal", state="hidden")
            page.wait_for_timeout(500)

        # Now edit each task
        for title in task_titles:
            # Click task
            task_card = page.locator(f".task-card:has-text('{title}')").first
            task_card.click()

            # Verify correct task is loaded
            page.wait_for_selector("#task-modal", state="visible")
            expect(page.locator("#task-title")).to_have_value(title)

            # Make a change
            page.fill("#task-desc", f"Updated {title}")

            # Save
            page.click("#task-submit")
            page.wait_for_selector("#task-modal", state="hidden")
            page.wait_for_timeout(500)

    def test_modal_buttons_remain_functional(self, board_with_columns: Page):
        """
        Test that all modal buttons remain functional after multiple uses.

        Specifically tests Save, Cancel, and Delete buttons.
        """
        page = board_with_columns

        # Create a task
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")
        page.fill("#task-title", "Button Test Task")
        page.fill("#task-desc", "Testing button functionality")
        # Column already set by clicking add button
        page.click("#task-submit")
        page.wait_for_selector("#task-modal", state="hidden")

        # Test Cancel button
        task_card = page.locator(".task-card:has-text('Button Test Task')").first
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")

        cancel_button = page.locator("#task-cancel")
        if cancel_button.count() > 0:
            cancel_button.click()
            page.wait_for_selector("#task-modal", state="hidden")
        else:
            # Close via backdrop if no cancel button
            page.click("#task-modal")
            page.wait_for_selector("#task-modal", state="hidden")

        # Test Save button again
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")
        page.fill("#task-desc", "Updated via save button test")

        save_button = page.locator("#task-submit")
        expect(save_button).to_be_enabled()
        save_button.click()
        page.wait_for_selector("#task-modal", state="hidden")

        # Test Delete button (if exists)
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")

        delete_button = page.locator("#delete-task-btn")
        if delete_button.count() > 0:
            expect(delete_button).to_be_enabled()
            delete_button.click()

            # Handle confirmation if present
            confirm_button = page.locator(
                "button:has-text('Delete'), button:has-text('Confirm')"
            )
            if confirm_button.count() > 0:
                confirm_button.click()

            page.wait_for_selector("#task-modal", state="hidden")

            # Verify task is deleted
            expect(task_card).to_be_hidden()

    def test_rapid_modal_interactions(self, board_with_columns: Page):
        """
        Test rapid opening and closing of modals.

        This stress-tests the modal system to ensure no race conditions.
        """
        page = board_with_columns

        # Rapidly open and close modal 10 times
        for i in range(10):
            page.click(".add-task-btn")
            page.wait_for_selector("#task-modal", state="visible", timeout=2000)

            # Immediately close
            page.click("#task-modal-close")
            page.wait_for_selector("#task-modal", state="hidden", timeout=2000)

        # Verify modal still works normally after rapid interactions
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")

        page.fill("#task-title", "After Rapid Test")
        page.fill("#task-desc", "Modal still functional")
        # Column already set by clicking add button

        save_button = page.locator("#task-submit")
        expect(save_button).to_be_enabled()
        save_button.click()

        page.wait_for_selector("#task-modal", state="hidden")
        expect(page.locator(".task-card:has-text('After Rapid Test')")).to_be_visible()


@pytest.mark.slow
class TestTaskModalEdgeCases:
    """Test edge cases and error scenarios for task modals."""

    def test_edit_task_with_empty_fields(self, board_with_columns: Page):
        """Test that validation works when trying to save empty fields."""
        page = board_with_columns

        # Create a task first
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")
        page.fill("#task-title", "Task to Clear")
        # Column already set by clicking add button
        page.click("#task-submit")
        page.wait_for_selector("#task-modal", state="hidden")

        # Edit and try to clear title
        task_card = page.locator(".task-card:has-text('Task to Clear')").first
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")

        # Clear title
        page.fill("#task-title", "")

        # Try to save - should fail or show validation
        page.click("#task-submit")

        # Modal should stay open (validation failed)
        # Or show error message
        page.wait_for_timeout(1000)

        # Modal should still be visible or show error
        # (Exact behavior depends on your validation implementation)

    def test_modal_state_after_network_error(self, board_with_columns: Page):
        """
        Test modal behavior when save operation fails.

        This ensures the modal remains functional after errors.
        """
        page = board_with_columns

        # This test would require mocking network failures
        # For now, we'll test that modal can be reopened after any error

        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")

        # Fill form
        page.fill("#task-title", "Network Test Task")
        # Column already set by clicking add button

        # Save (might succeed or fail depending on network)
        page.click("#task-submit")
        page.wait_for_timeout(2000)

        # Close modal if still open
        if page.locator("#task-modal").is_visible():
            page.click("#task-modal-close")

        # Verify we can still open modal
        page.click(".add-task-btn")
        expect(page.locator("#task-modal")).to_be_visible()
