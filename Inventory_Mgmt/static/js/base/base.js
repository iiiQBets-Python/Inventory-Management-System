function closeSidebar(sidebarId) {
    document.getElementById(sidebarId).style.right = '-350px';
  }
  
  document.getElementById('profileLink').addEventListener('click', function (event) {
    event.preventDefault();
    document.getElementById('profileSidebar').style.right = '0';
    document.getElementById('notificationSidebar').style.right = '-350px';
    document.getElementById('inboxSidebar').style.right = '-350px';
  });
  
  document.getElementById('notificationLink').addEventListener('click', function (event) {
    event.preventDefault();
    document.getElementById('notificationSidebar').style.right = '0';
    document.getElementById('profileSidebar').style.right = '-350px';
    document.getElementById('inboxSidebar').style.right = '-350px';
  });
  
  document.getElementById('inboxLink').addEventListener('click', function (event) {
    event.preventDefault();
    document.getElementById('inboxSidebar').style.right = '0';
    document.getElementById('profileSidebar').style.right = '-350px';
    document.getElementById('notificationSidebar').style.right = '-350px';
  });
  
  // Close sidebar when clicking outside of it
  document.addEventListener('click', function (event) {
    const profileSidebar = document.getElementById('profileSidebar');
    const notificationSidebar = document.getElementById('notificationSidebar');
    const inboxSidebar = document.getElementById('inboxSidebar');
  
    if (!event.target.closest('#profileLink') && !event.target.closest('#profileSidebar')) {
        profileSidebar.style.right = '-350px';
    }
    if (!event.target.closest('#notificationLink') && !event.target.closest('#notificationSidebar')) {
        notificationSidebar.style.right = '-350px';
    }
    if (!event.target.closest('#inboxLink') && !event.target.closest('#inboxSidebar')) {
        inboxSidebar.style.right = '-350px';
    }
  });
  
  function deleteNotification(button) {
    const card = button.closest('.notification');
    card.classList.add('deleted');
    setTimeout(() => {
        card.remove();
    }, 200);
    event.stopPropagation();
  }
  
  function deleteMessage(button) {
    const card = button.closest('.inbox');
    card.classList.add('deleted');
    setTimeout(() => {
        card.remove();
    }, 200);
    event.stopPropagation();
  }
  
  ////////////////////////////////////////////////////////////////////////////////////////
  //                            Side Menubar JS
  ////////////////////////////////////////////////////////////////////////////////////////
  
  function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.toggle-btn');
    const submenus = document.querySelectorAll('.submenu'); // Get all submenus
  
    sidebar.classList.toggle('collapsed');
  
    // Update the visibility of menu text and submenu based on sidebar state
    const menuTexts = document.querySelectorAll('.menu-text');
    if (sidebar.classList.contains('collapsed')) {
        menuTexts.forEach(text => text.style.display = 'none');
        submenus.forEach(submenu => submenu.style.display = 'none'); // Close submenus when sidebar is collapsed
        toggleBtn.innerText = '☰';
    } else {
        menuTexts.forEach(text => text.style.display = 'inline');
        toggleBtn.innerText = '✖';
    }
  }
  
  document.addEventListener('DOMContentLoaded', function () {
    // Function to set the active state
    function setActiveMenuItem() {
        const currentPath = window.location.pathname;
        document.querySelectorAll('.menu-item, .submenu-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href') === currentPath) {
                item.classList.add('active');
                const parentMenu = item.closest('.submenu');
                if (parentMenu) {
                    parentMenu.style.display = 'block';
                    parentMenu.previousElementSibling.classList.add('active');
                }
            }
        });
    }
  
    // Call setActiveMenuItem on page load to set the initial active state
    setActiveMenuItem();
  
    // Function to deactivate all menu and submenu items
    function deactivateAll() {
        document.querySelectorAll('.menu-item, .submenu-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelectorAll('.submenu').forEach(submenu => {
            submenu.style.display = 'none';
        });
    }
  
    // Event listener for menu items
    document.querySelectorAll('.menu-item').forEach(item => {
      item.addEventListener('click', function (event) {
          const sidebar = document.querySelector('.sidebar');
          const submenu = item.nextElementSibling;
  
          if (sidebar.classList.contains('collapsed')) {
              sidebar.classList.remove('collapsed');
              const menuTexts = document.querySelectorAll('.menu-text');
              menuTexts.forEach(text => text.style.display = 'inline');
              const submenus = document.querySelectorAll('.submenu');
              submenus.forEach(submenu => submenu.style.display = 'none'); // Close submenus when sidebar is collapsed
              toggleBtn.innerText = '✖';
              // Expand the clicked submenu
              if (submenu && submenu.classList.contains('submenu')) {
                  submenu.style.display = 'block';
              }
          } else {
              // Toggle the visibility of the submenu
              if (submenu && submenu.classList.contains('submenu')) {
                  if (submenu.style.display === 'block') {
                      submenu.style.display = 'none';
                  } else {
                      deactivateAll(); // Close previously selected menu and submenu
                      submenu.style.display = 'block'; // Open the new submenu
                      item.classList.add('active'); // Activate the clicked menu item
                  }
              }
          }
      });
  });
  
  
    // Event listener for submenu items
    document.querySelectorAll('.submenu-item').forEach(item => {
      item.addEventListener('click', function (event) {
          deactivateAll();
          item.classList.add('active');
          const parentMenu = item.closest('.submenu');
          if (parentMenu) {
              parentMenu.style.display = 'block';
              parentMenu.previousElementSibling.classList.add('active');
          }
      });
    });
  
    // Ensure active state is maintained on page load
    window.addEventListener('load', setActiveMenuItem);
  });
  
  
  // Hover effect for collapsed sidebar
  document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('mouseenter', function () {
        if (document.querySelector('.sidebar').classList.contains('collapsed')) {
            const tooltip = document.createElement('span');
            tooltip.className = 'menu-tooltip';
            tooltip.innerText = item.querySelector('.menu-text').innerText;
            document.body.appendChild(tooltip);
  
            const rect = item.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            tooltip.style.left = `${rect.right}px`;
            tooltip.style.top = `${rect.top + window.scrollY + (rect.height - tooltipRect.height) / 2}px`;
        }
    });
  
    item.addEventListener('mouseleave', function () {
        const tooltip = document.querySelector('.menu-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    });
  });
  