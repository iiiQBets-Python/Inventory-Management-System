document.getElementById('imageInput').addEventListener('change', function() {
    var fileName = this.files[0].name;
    var label = document.querySelector('.upload-label');
    label.innerText = fileName;
  });

  document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('imageInput');
    const dragDropArea = document.getElementById('dragDropArea');

    dragDropArea.addEventListener('dragover', function(e) {
      e.preventDefault();
      this.classList.add('dragover');
    });

    dragDropArea.addEventListener('dragleave', function() {
      this.classList.remove('dragover');
    });

    dragDropArea.addEventListener('drop', function(e) {
      e.preventDefault();
      this.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      handleImageUpload(file);
    });

    imageInput.addEventListener('change', function() {
      const file = this.files[0];
      handleImageUpload(file);
    });


    function handleImageUpload(file) {
      const reader = new FileReader();
      reader.onload = function(e) {
        imagePreview.src = e.target.result;
      };
      reader.readAsDataURL(file);
    }
  });
  function clearForm() {
    document.getElementById("product_id").value = "";
    document.getElementById("category_name").value = "";
    document.getElementById("product_name").value = "";
    document.getElementById("sku").value = "";
    document.getElementById("unit").value = "";
    document.getElementById("weight").value = "";
    document.getElementById("weightUnit").value = "";
    document.getElementById("length").value = "";
    document.getElementById("width").value = "";
    document.getElementById("height").value = "";
    document.getElementById("dimensionUnit").value = "";
    document.getElementById("cost_price").value = "";
    document.getElementById("selling_price").value = "";
    document.getElementById("manufacturer_name").value = "";
    document.getElementById("brand_name").value = "";
    document.getElementById("upc").value = "";
    document.getElementById("ean").value = "";
    document.getElementById("mpn").value = "";
    document.getElementById("description").value = "";
    document.getElementById("is_available").checked = true;
  }