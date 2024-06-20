$(document).ready(function() {
    $('#product_name').change(function() {
      var selectedProduct = $(this).find(':selected');
      $('#upc').val(selectedProduct.data('upc'));
      $('#mpn').val(selectedProduct.data('mpn'));
      $('#ean').val(selectedProduct.data('ean'));
    });
  });

  function clearForm() {
    document.getElementById("manufacturer_name").value = "";
    document.getElementById("brand_name").value = "";
    document.getElementById("product_name").value = "";
    document.getElementById("stock_num").value = "";
    document.getElementById("stock_status").value = "";
    document.getElementById("min_stock").value = "";
    document.getElementById("upc").value = "";
    document.getElementById("ean").value = "";
    document.getElementById("mpn").value = "";
  }
