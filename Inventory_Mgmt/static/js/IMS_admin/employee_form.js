    // Function to enable form fields upon selecting a department
    function enableForm() {
        var department = document.getElementById("department_name").value;
        if (department) {
          document.getElementById("employeeInfoSection").style.display = "block";
        } else {
          document.getElementById("employeeInfoSection").style.display = "none";
        }
      }
  
      // Function to clear the form
      function clearForm() {
          document.getElementById("department_name").value = "";
          document.getElementById("first_name").value = "";
          document.getElementById("last_name").value = "";
          document.getElementById("email").value = "";
          document.getElementById("address").value = "";
          document.getElementById("phone_num").value = "";
          document.getElementById("designation").value = "";
          document.getElementById("date_of_join").value = "";
          document.getElementById("employeeInfoSection").style.display = "none";
        }
  
        document.addEventListener('DOMContentLoaded', function() {
          const dragDropArea = document.getElementById('dragDropArea');
    
          ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, preventDefaults, false);
          });
    
          ['dragenter', 'dragover'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, highlight, false);
          });
    
          ['dragleave', 'drop'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, unhighlight, false);
          });
    
          dragDropArea.addEventListener('drop', handleDrop, false);
        });
    
        function preventDefaults(e) {
          e.preventDefault();
          e.stopPropagation();
        }
    
        function highlight() {
          this.classList.add('dragover');
        }
    
        function unhighlight() {
          this.classList.remove('dragover');
        }
    
        function handleDrop(e) {
          const fileList = e.dataTransfer.files;
          handleImageChange(fileList);
        }
    
        function handleImageChange(files) {
          const file = files[0]; // Only consider the first file
          const fileList = document.getElementById('fileList');
      
          if (file) {
              const listItem = document.createElement("li");
      
              // Create a span element for the image icon
              const imageIcon = document.createElement("i");
              imageIcon.className = "fas fa-image mr-2"; // Add necessary classes for the icon
      
              // Create a text node with the file name
              const fileNameNode = document.createTextNode(file.name);
      
              // Append icon and file name to the list item
              listItem.appendChild(imageIcon);
              listItem.appendChild(fileNameNode);
      
              // Click event to open the image in a new tab when the list item is clicked
              listItem.addEventListener('click', function() {
                  window.open(URL.createObjectURL(file), '_blank'); // Open image in a new tab
              });
      
              // Create a button to remove the image from the list
              const cancelBtn = document.createElement("span");
              cancelBtn.innerHTML = "<i class='fas fa-times-circle' style='color: red;'></i>";
              cancelBtn.className = "cancel-btn";
              cancelBtn.onclick = function() {
                  fileList.removeChild(listItem); // Remove the list item when cancel button is clicked
              };
      
              // Append cancel button to the list item
              listItem.appendChild(cancelBtn);
      
              // Append the list item to the file list
              fileList.appendChild(listItem);
          }
      }
      
      
      function handleFileSelect(files) {
          handleImageChange(files);
      }
        
  
      function saveAndSelectDepartment() {
      var formData = $("#addDepartmentForm").serialize(); // Serialize the form data
      $.ajax({
          type: "POST",
          url: "{% url 'add_department' %}", // URL to which the form data will be sent
          data: formData, // Form data
          success: function(response) {
            alert("Department Registration Successfull")
              var newDepartmentId = response.department_id;
              var newDepartmentName = response.department_name;
              var selectElement = document.getElementById("department_name");
              var option = document.createElement("option");
              option.text = newDepartmentName;
              option.value = newDepartmentId;
              selectElement.add(option);
              $('#addDepartmentModal').modal('hide');
              document.getElementById("new_department_id").value = ""; // Clear the department ID field
              document.getElementById("new_department_name").value = ""; // Clear the department name field
          },
          error: function(xhr, errmsg, err) {
              console.log(xhr.status + ": " + xhr.responseText); // Log any errors
          }
      });
  }
  
  
    
    document.getElementById('button-addon2').addEventListener('click', function() {
      $('#addDepartmentModal').modal('show');
    });
   
    $(document).ready(function() {
      // Function to handle form submission
      $('#employeeForm').submit(function(e) {
        e.preventDefault(); // Prevent default form submission
        var formData = $(this).serialize(); // Serialize form data
  
        // AJAX request to submit form data
        $.ajax({
          type: 'POST',
          url: $(this).attr('action'), // URL to which the form data will be sent
          data: formData, // Form data
          success: function(response) {
            // Display success message
            alert('Employee registration successful!');
            // Optionally, you can reset the form here
            $('#employeeForm')[0].reset();
          },
          error: function(xhr, errmsg, err) {
            console.log(xhr.status + ': ' + xhr.responseText); // Log any errors
          }
        });
      });
    });
  