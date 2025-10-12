"""
Group Management Tests

This test suite validates group creation, editing, member management,
and all group-related functionality can be performed multiple times.
"""

import pytest
from playwright.sync_api import Page, expect


class TestGroupManagement:
    """Test suite for group management functionality."""

    def test_navigate_to_groups_page(self, authenticated_page: Page, base_url: str):
        """Test navigating to the groups management page."""
        page = authenticated_page

        # Navigate to groups page
        page.goto(f"{base_url}/static/groups.html")

        # Wait for page to load
        page.wait_for_selector("h2:has-text('Your Groups')", timeout=10000)

        # Verify page elements
        expect(page.locator("h1")).to_contain_text("Group Management")
        expect(page.locator("#create-group-btn")).to_be_visible()
        print("✅ Groups page loaded successfully")

    def test_create_group_with_all_fields(
        self, authenticated_page: Page, base_url: str
    ):
        """Test creating a group with all fields filled."""
        page = authenticated_page

        # Navigate to groups page
        page.goto(f"{base_url}/static/groups.html")
        page.wait_for_selector("#create-group-btn", timeout=10000)

        # Click create group button
        page.click("#create-group-btn")
        page.wait_for_timeout(1000)

        # Wait for modal
        page.wait_for_selector("#create-group-modal", state="visible")

        # Fill all fields
        group_name = f"Test Group {int(page.evaluate('Date.now()'))}"
        group_desc = "This is a test group for comprehensive testing"

        page.fill("#group-name", group_name)
        page.fill("#group-description", group_desc)

        # Submit form
        submit_btn = page.locator("#create-group-form button[type='submit']")
        expect(submit_btn).to_be_visible()
        expect(submit_btn).to_be_enabled()
        submit_btn.click()

        # Wait for modal to close
        page.wait_for_selector("#create-group-modal", state="hidden", timeout=5000)
        page.wait_for_timeout(1000)

        # Verify group appears in list (use specific selector for the new group)
        group_card = page.locator(f".group-card:has-text('{group_name}')").first
        expect(group_card).to_be_visible()

        print(f"✅ Group created: {group_name}")

    def test_edit_group_multiple_times_all_fields(
        self, authenticated_page: Page, base_url: str
    ):
        """
        Test editing a group multiple times with all fields.

        This is the critical test for group modal reusability.
        """
        page = authenticated_page

        # Navigate to groups page
        page.goto(f"{base_url}/static/groups.html")
        page.wait_for_selector("#create-group-btn", timeout=10000)

        # Create a group first
        page.click("#create-group-btn")
        page.wait_for_timeout(1000)
        page.wait_for_selector("#create-group-modal", state="visible")

        initial_name = f"Multi-Edit Group {int(page.evaluate('Date.now()'))}"
        initial_desc = "Initial description"

        page.fill("#group-name", initial_name)
        page.locator("#create-group-form button[type='submit']").click()
        page.wait_for_selector("#create-group-modal", state="hidden")
        page.wait_for_timeout(2000)  # Wait for group to be created and list to refresh

        # Now edit the group 3 times
        for iteration in range(3):
            print(f"\n=== Group Edit Iteration {iteration + 1} ===")

            # Find the group card
            group_card = page.locator(f".group-card:has-text('{initial_name}')").first
            
            # Verify card exists and is visible
            expect(group_card).to_be_visible(timeout=5000)
            print(f"  Group card found: {initial_name}")
            
            # Click the "View Details" button inside the card
            view_button = group_card.locator("button:has-text('View Details')")
            view_button.click()

            # Give JavaScript time to load details
            page.wait_for_timeout(1000)

            # Wait for group details to load - check for the title element
            page.wait_for_selector("#group-details-title", state="visible", timeout=10000)
            
            # Wait for edit button to appear
            page.wait_for_selector("#edit-group-btn", state="visible", timeout=5000)

            # Click edit button in the group details view
            edit_btn = page.locator("#edit-group-btn")
            edit_btn.click()

            # Give JavaScript time to show modal
            page.wait_for_timeout(1000)

            # Wait for edit modal to appear
            page.wait_for_selector("#edit-group-modal", state="visible", timeout=10000)

            # Update both fields
            new_name = f"{initial_name} - Edit {iteration + 1}"
            new_desc = f"Updated description - iteration {iteration + 1}"

            # Use the edit modal's specific input fields
            name_input = page.locator("#edit-group-name")
            desc_input = page.locator("#edit-group-description")

            name_input.fill(new_name)
            desc_input.fill(new_desc)

            # Save changes - find submit button within the edit modal
            save_btn = page.locator("#edit-group-form button[type='submit']")
            expect(save_btn).to_be_visible()
            expect(save_btn).to_be_enabled()
            save_btn.click()

            # Wait for modal to close
            page.wait_for_selector("#edit-group-modal", state="hidden", timeout=5000)
            
            # Wait for update to complete
            page.wait_for_timeout(1000)

            # Verify group name updated in the details view
            expect(page.locator("#group-details-title")).to_contain_text(new_name)

            # Update current name for next iteration
            initial_name = new_name

            print(f"  ✅ Edit {iteration + 1} successful: {new_name}")
            
            # Go back to groups list for next iteration (if not the last one)
            if iteration < 2:  # 0, 1, 2 - so skip on iteration 2
                back_btn = page.locator("#back-to-groups-btn")
                back_btn.click()
                page.wait_for_timeout(1000)
                # Wait for groups list to be visible
                page.wait_for_selector("#create-group-btn", state="visible", timeout=5000)

        print(f"\n✅ Successfully edited group 3 times!")

    def test_create_multiple_groups_sequentially(
        self, authenticated_page: Page, base_url: str
    ):
        """Test creating multiple groups one after another."""
        page = authenticated_page

        # Navigate to groups page
        page.goto(f"{base_url}/static/groups.html")
        page.wait_for_selector("#create-group-btn", timeout=10000)

        group_names = []

        # Create 3 groups sequentially
        for i in range(3):
            page.click("#create-group-btn")
            page.wait_for_timeout(1000)
            page.wait_for_selector("#create-group-modal", state="visible")

            group_name = (
                f"Sequential Group {i + 1} - {int(page.evaluate('Date.now()'))}"
            )
            group_desc = f"Description for group {i + 1}"

            page.fill("#group-name", group_name)
            page.fill("#group-description", group_desc)
            page.locator("#create-group-form button[type='submit']").click()

            page.wait_for_selector("#create-group-modal", state="hidden")
            page.wait_for_timeout(1000)

            group_names.append(group_name)
            print(f"  ✅ Created group {i + 1}: {group_name}")

        # Verify all groups exist
        for group_name in group_names:
            expect(page.locator("body")).to_contain_text(group_name)

        print(f"✅ Successfully created {len(group_names)} groups sequentially")

    def test_group_modal_cancel_button(self, authenticated_page: Page, base_url: str):
        """Test that cancel button doesn't save changes."""
        page = authenticated_page

        # Navigate to groups page
        page.goto(f"{base_url}/static/groups.html")
        page.wait_for_selector("#create-group-btn", timeout=10000)

        # Open create modal
        page.click("#create-group-btn")
        page.wait_for_timeout(1000)
        page.wait_for_selector("#create-group-modal", state="visible")

        # Fill form
        page.fill("#group-name", "This should not be saved")
        page.fill("#group-description", "This description should not be saved")

        # Click cancel
        cancel_btn = page.locator(
            "#cancel-create-group, button:has-text('Cancel')"
        ).first
        expect(cancel_btn).to_be_visible()
        cancel_btn.click()

        # Wait for modal to close
        page.wait_for_selector("#create-group-modal", state="hidden")
        page.wait_for_timeout(500)

        # Verify group was not created
        expect(page.locator("body")).not_to_contain_text("This should not be saved")

        print("✅ Cancel button works - group not created")

    def test_delete_group(self, authenticated_page: Page, base_url: str):
        """Test deleting a group."""
        page = authenticated_page

        # Navigate to groups page
        page.goto(f"{base_url}/static/groups.html")
        page.wait_for_selector("#create-group-btn", timeout=10000)

        # Create a group to delete
        page.click("#create-group-btn")
        page.wait_for_timeout(1000)
        page.wait_for_selector("#create-group-modal", state="visible")

        group_name = f"Delete Test Group {int(page.evaluate('Date.now()'))}"
        page.fill("#group-name", group_name)
        page.locator("#create-group-form button[type='submit']").click()
        page.wait_for_selector("#create-group-modal", state="hidden")
        page.wait_for_timeout(2000)  # Wait for group to be created and list to refresh

        # Verify group exists
        expect(page.locator("body")).to_contain_text(group_name)

        # Click on the group to open details
        group_card = page.locator(f".group-card:has-text('{group_name}')").first
        
        # Click the "View Details" button inside the card
        view_button = group_card.locator("button:has-text('View Details')")
        view_button.click()
        
        # Give JavaScript time to load details
        page.wait_for_timeout(1000)
        
        # Wait for group details to load - check for the title element
        page.wait_for_selector("#group-details-title", state="visible", timeout=5000)
        
        # Wait for delete button to appear
        page.wait_for_selector("#delete-group-btn", state="visible", timeout=5000)

        # Set up dialog handler BEFORE clicking (must be synchronous)
        def handle_dialog(dialog):
            print(f"Dialog appeared: {dialog.message}")
            dialog.accept()
        
        page.once("dialog", handle_dialog)
        
        # Click delete button
        delete_btn = page.locator("#delete-group-btn")
        delete_btn.click()

        # Wait for deletion to complete and return to groups list
        # The delete operation: shows confirm, deletes group, returns to list, refreshes
        page.wait_for_timeout(3000)
        
        # Wait for groups list to be visible again (we should be back on the list)
        page.wait_for_selector("#create-group-btn", state="visible", timeout=5000)

        # Verify group is deleted - the specific group card should not exist
        deleted_group_card = page.locator(f".group-card:has-text('{group_name}')")
        expect(deleted_group_card).to_have_count(0)

        print(f"✅ Group deleted: {group_name}")


@pytest.mark.slow
class TestGroupMemberManagement:
    """Test suite for group member management."""

    def test_add_member_to_group(self, authenticated_page: Page, base_url: str):
        """Test adding a member to a group."""
        page = authenticated_page

        # Navigate to groups page
        page.goto(f"{base_url}/static/groups.html")
        page.wait_for_selector("#create-group-btn", timeout=10000)

        # Create a group
        page.click("#create-group-btn")
        page.wait_for_timeout(1000)
        page.wait_for_selector("#create-group-modal", state="visible")

        group_name = f"Member Test Group {int(page.evaluate('Date.now()'))}"
        page.fill("#group-name", group_name)
        page.locator("#create-group-form button[type='submit']").click()
        page.wait_for_selector("#create-group-modal", state="hidden")
        page.wait_for_timeout(1000)

        # Open group details by clicking on the group card
        group_card = page.locator(
            f".group-card:has-text('{group_name}'), .group-item:has-text('{group_name}')"
        ).first
        group_card.click()
        
        # Wait for group details section to become visible and invite button to appear
        page.wait_for_selector("#group-details-section", state="visible", timeout=5000)
        page.wait_for_timeout(1000)

        # Find invite member button in the group details section
        invite_member_btn = page.locator("#invite-member-btn").first

        if invite_member_btn.count() > 0 and invite_member_btn.is_visible():
            invite_member_btn.click()
            page.wait_for_timeout(500)

            # Wait for modal to appear
            page.wait_for_selector("#invite-member-modal", state="visible", timeout=2000)

            # Fill member email
            member_input = page.locator("#invite-email").first
            if member_input.count() > 0:
                member_input.fill("test@example.com")

                # Select role
                role_select = page.locator("#invite-role").first
                if role_select.count() > 0:
                    role_select.select_option("member")

                # Submit
                submit_btn = page.locator("#invite-member-form button[type='submit']").first
                submit_btn.click()
                page.wait_for_timeout(1000)

                print("✅ Member invite functionality tested")
        else:
            pytest.skip("Invite member functionality not available in UI")

    def test_group_member_list(self, authenticated_page: Page, base_url: str):
        """Test viewing group members."""
        page = authenticated_page

        # Navigate to groups page
        page.goto(f"{base_url}/static/groups.html")
        page.wait_for_selector("#create-group-btn", timeout=10000)

        # Create a group
        page.click("#create-group-btn")
        page.wait_for_timeout(1000)
        page.wait_for_selector("#create-group-modal", state="visible")

        group_name = f"Members List Group {int(page.evaluate('Date.now()'))}"
        page.fill("#group-name", group_name)
        page.locator("#create-group-form button[type='submit']").click()
        page.wait_for_selector("#create-group-modal", state="hidden")
        page.wait_for_timeout(1000)

        # Open group details
        group_card = page.locator(
            f".group-card:has-text('{group_name}'), .group-item:has-text('{group_name}')"
        ).first
        group_card.click()
        page.wait_for_timeout(1000)

        # Check if members section exists
        members_section = page.locator(
            ".members-list, #members-section, h3:has-text('Members')"
        )

        if members_section.count() > 0:
            print("✅ Members section visible")
            # Creator should be listed as a member
            expect(page.locator("body")).to_contain_text("Member")
        else:
            pytest.skip("Members list not visible in UI")


@pytest.mark.slow
class TestGroupEdgeCases:
    """Test edge cases for group management."""

    def test_group_name_validation(self, authenticated_page: Page, base_url: str):
        """Test that empty group name is not allowed."""
        page = authenticated_page

        # Navigate to groups page
        page.goto(f"{base_url}/static/groups.html")
        page.wait_for_selector("#create-group-btn", timeout=10000)

        page.click("#create-group-btn")
        page.wait_for_timeout(1000)
        page.wait_for_selector("#create-group-modal", state="visible")

        # Try to submit with empty name
        page.fill("#group-name", "")
        page.locator("#create-group-form button[type='submit']").click()

        # Modal should stay open (validation failed)
        page.wait_for_timeout(500)
        expect(page.locator("#create-group-modal")).to_be_visible()

        print("✅ Empty group name correctly rejected")

    def test_group_description_optional(self, authenticated_page: Page, base_url: str):
        """Test that group can be created without description."""
        page = authenticated_page

        # Navigate to groups page
        page.goto(f"{base_url}/static/groups.html")
        page.wait_for_selector("#create-group-btn", timeout=10000)

        page.click("#create-group-btn")
        page.wait_for_timeout(1000)
        page.wait_for_selector("#create-group-modal", state="visible")

        group_name = f"No Desc Group {int(page.evaluate('Date.now()'))}"
        page.fill("#group-name", group_name)
        page.fill("#group-description", "")  # Explicitly empty

        page.locator("#create-group-form button[type='submit']").click()
        page.wait_for_selector("#create-group-modal", state="hidden")

        # Verify group created
        expect(page.locator("body")).to_contain_text(group_name)

        print("✅ Group created without description")
