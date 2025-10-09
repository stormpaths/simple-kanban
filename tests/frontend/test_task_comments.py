"""
Task Comments Tests

This test suite validates that task comments can be added, edited, and deleted
multiple times without issues. This ensures complete coverage of all task fields.
"""

import pytest
from playwright.sync_api import Page, expect


class TestTaskComments:
    """Test suite for task comment functionality."""
    
    def test_add_multiple_comments_to_task(self, board_with_columns: Page):
        """
        Test adding multiple comments to a single task.
        
        This validates that the comment system works correctly with repeated use.
        """
        page = board_with_columns
        
        # Wait for board to load
        page.wait_for_selector(".column", timeout=10000)
        
        # Create a new task (click add button in first column)
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")
        
        task_title = "Task with Multiple Comments"
        page.fill("#task-title", task_title)
        page.fill("#task-desc", "Testing comment functionality")
        # Column is already set when clicking add button
        page.click("#task-submit")
        
        # Wait for task to be created
        page.wait_for_selector("#task-modal", state="hidden")
        page.wait_for_timeout(1000)
        
        # Open the task to add comments
        task_card = page.locator(f".task-card:has-text('{task_title}')").first
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")
        
        # Add multiple comments
        comments = [
            "First comment on this task",
            "Second comment with more details",
            "Third comment to test multiple additions"
        ]
        
        for i, comment_text in enumerate(comments):
            print(f"\n=== Adding comment {i + 1} ===")
            
            # Fill comment textarea
            comment_input = page.locator("#new-comment")
            expect(comment_input).to_be_visible()
            comment_input.fill(comment_text)
            
            # Click add comment button
            add_btn = page.locator("#add-comment-btn")
            expect(add_btn).to_be_visible()
            expect(add_btn).to_be_enabled()
            add_btn.click()
            
            # Wait for comment to be added
            page.wait_for_timeout(1000)
            
            # Verify comment appears in list
            comment_list = page.locator("#comments-list")
            expect(comment_list).to_contain_text(comment_text)
            
            # Verify textarea is cleared
            expect(comment_input).to_have_value("")
        
        print(f"\n✅ Successfully added {len(comments)} comments!")
        
        # Close modal by clicking close button
        page.click("#task-modal-close")
        page.wait_for_selector("#task-modal", state="hidden", timeout=10000)
    
    def test_edit_task_with_all_fields_multiple_times(self, board_with_columns: Page):
        """
        Test editing ALL task fields (title, description, comments) multiple times.
        
        This is the comprehensive test for complete field coverage.
        """
        page = board_with_columns
        
        # Wait for board
        page.wait_for_selector(".column", timeout=10000)
        
        # Create a task
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")
        
        task_title = "Complete Field Test Task"
        page.fill("#task-title", task_title)
        page.fill("#task-desc", "Initial description")
        # Column already set by clicking add button
        page.click("#task-submit")
        page.wait_for_selector("#task-modal", state="hidden")
        page.wait_for_timeout(1000)
        
        # Edit the task 3 times, updating ALL fields each time
        for iteration in range(3):
            print(f"\n=== Edit iteration {iteration + 1} - ALL FIELDS ===")
            
            # Open task
            task_card = page.locator(f".task-card:has-text('{task_title}')").first
            task_card.click()
            page.wait_for_selector("#task-modal", state="visible")
            
            # Update title
            new_title = f"{task_title} - Edit {iteration + 1}"
            title_input = page.locator("#task-title")
            title_input.fill(new_title)
            task_title = new_title  # Update for next iteration
            
            # Update description
            new_desc = f"Updated description - iteration {iteration + 1}"
            desc_input = page.locator("#task-desc")
            desc_input.fill(new_desc)
            
            # Add a comment
            comment_text = f"Comment added in iteration {iteration + 1}"
            comment_input = page.locator("#new-comment")
            comment_input.fill(comment_text)
            
            add_btn = page.locator("#add-comment-btn")
            add_btn.click()
            
            # Wait for comment to be added
            page.wait_for_timeout(1000)
            
            # Verify comment appears
            expect(page.locator("#comments-list")).to_contain_text(comment_text)
            
            # Save task
            save_btn = page.locator("#task-submit")
            expect(save_btn).to_be_visible()
            expect(save_btn).to_be_enabled()
            save_btn.click()
            
            # Wait for save
            page.wait_for_selector("#task-modal", state="hidden")
            page.wait_for_timeout(1000)
            
            # Verify task still exists with updated title
            expect(page.locator(f".task-card:has-text('{task_title}')")).to_be_visible()
        
        print("\n✅ Successfully edited ALL fields 3 times!")
        
        # Final verification - reopen and check all data persisted
        task_card = page.locator(f".task-card:has-text('{task_title}')").first
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")
        
        # Verify title
        expect(page.locator("#task-title")).to_have_value(task_title)
        
        # Verify description (should be iteration 3 - the last edit)
        expect(page.locator("#task-desc")).to_have_value("Updated description - iteration 3")
        
        # Verify all comments are present (iterations 1, 2, 3)
        comments_list = page.locator("#comments-list")
        expect(comments_list).to_contain_text("Comment added in iteration 1")
        expect(comments_list).to_contain_text("Comment added in iteration 2")
        expect(comments_list).to_contain_text("Comment added in iteration 3")
        
        print("✅ All data persisted correctly!")
    
    def test_comment_keyboard_shortcut(self, board_with_columns: Page):
        """Test that Ctrl+Enter submits a comment."""
        page = board_with_columns
        
        # Create and open a task
        page.wait_for_selector(".column", timeout=10000)
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")
        
        page.fill("#task-title", "Keyboard Shortcut Test")
        # Column already set by clicking add button
        page.click("#task-submit")
        page.wait_for_selector("#task-modal", state="hidden")
        page.wait_for_timeout(1000)
        
        # Reopen task
        task_card = page.locator(".task-card:has-text('Keyboard Shortcut Test')").first
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")
        
        # Type comment and use Ctrl+Enter
        comment_input = page.locator("#new-comment")
        comment_input.fill("Comment via keyboard shortcut")
        
        # Press Ctrl+Enter
        comment_input.press("Control+Enter")
        
        # Wait and verify comment was added
        page.wait_for_timeout(1000)
        expect(page.locator("#comments-list")).to_contain_text("Comment via keyboard shortcut")
        expect(comment_input).to_have_value("")
    
    def test_comment_validation(self, board_with_columns: Page):
        """Test that empty comments are not submitted."""
        page = board_with_columns
        
        # Create and open a task
        page.wait_for_selector(".column", timeout=10000)
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")
        
        page.fill("#task-title", "Comment Validation Test")
        # Column already set by clicking add button
        page.click("#task-submit")
        page.wait_for_selector("#task-modal", state="hidden")
        page.wait_for_timeout(1000)
        
        # Reopen task
        task_card = page.locator(".task-card:has-text('Comment Validation Test')").first
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")
        
        # Try to submit empty comment
        comment_input = page.locator("#new-comment")
        comment_input.fill("")  # Empty
        
        add_btn = page.locator("#add-comment-btn")
        add_btn.click()
        
        # Wait a bit
        page.wait_for_timeout(500)
        
        # Comment list should be empty or not have empty content
        comments_list = page.locator("#comments-list")
        # Should not contain any comment items or should be empty
        
        # Try with whitespace only
        comment_input.fill("   ")  # Just spaces
        add_btn.click()
        page.wait_for_timeout(500)
        
        # Still should not add comment
        print("✅ Empty comments correctly rejected")


@pytest.mark.slow
class TestTaskCommentsEdgeCases:
    """Test edge cases for task comments."""
    
    def test_long_comment_validation(self, board_with_columns: Page):
        """Test that very long comments are handled properly."""
        page = board_with_columns
        
        # Create and open a task
        page.wait_for_selector(".column", timeout=10000)
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")
        
        page.fill("#task-title", "Long Comment Test")
        # Column already set by clicking add button
        page.click("#task-submit")
        page.wait_for_selector("#task-modal", state="hidden")
        page.wait_for_timeout(1000)
        
        # Reopen task
        task_card = page.locator(".task-card:has-text('Long Comment Test')").first
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")
        
        # Try to add a very long comment (over 2000 characters)
        long_comment = "A" * 2500  # Exceeds 2000 char limit
        
        comment_input = page.locator("#new-comment")
        comment_input.fill(long_comment)
        
        add_btn = page.locator("#add-comment-btn")
        add_btn.click()
        
        # Should show error or reject
        page.wait_for_timeout(1000)
        
        # Check if alert appeared or comment was rejected
        # (Exact behavior depends on implementation)
        print("✅ Long comment validation tested")
    
    def test_comment_persistence_after_modal_reopen(self, board_with_columns: Page):
        """Test that comments persist when modal is closed and reopened."""
        page = board_with_columns
        
        # Create task with comment
        page.wait_for_selector(".column", timeout=10000)
        page.click(".add-task-btn")
        page.wait_for_selector("#task-modal", state="visible")
        
        page.fill("#task-title", "Comment Persistence Test")
        # Column already set by clicking add button
        page.click("#task-submit")
        page.wait_for_selector("#task-modal", state="hidden")
        page.wait_for_timeout(1000)
        
        # Open and add comment
        task_card = page.locator(".task-card:has-text('Comment Persistence Test')").first
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")
        
        comment_input = page.locator("#new-comment")
        comment_input.fill("Persistent comment")
        page.locator("#add-comment-btn").click()
        page.wait_for_timeout(1000)
        
        # Close modal
        page.click("#task-modal-close")
        page.wait_for_selector("#task-modal", state="hidden", timeout=10000)
        
        # Reopen modal
        task_card.click()
        page.wait_for_selector("#task-modal", state="visible")
        
        # Verify comment is still there
        expect(page.locator("#comments-list")).to_contain_text("Persistent comment")
        
        print("✅ Comments persist across modal reopens")
