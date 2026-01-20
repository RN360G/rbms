
function displayAllCarts(transactionID){
    $.ajax({
        url: '/sales/salesdisplayallcarts',
        type: 'GET',
        dataType: 'json',
        data: {
            'transactionID': transactionID,
        },
        success: function (response){
            for(var i=0; i <= response.data.length; i++){
                if(response.data[i].quantity > 0)
                {
                    document.getElementById('cartPage'+ response.data[i].productRef__productCode).hidden=false;
                }
                else
                {
                    document.getElementById('cartPage'+ response.data[i].productRef__productCode).hidden=true;
                }

                document.getElementById('addQty'+ response.data[i].productRef__productCode).innerHTML = response.data[i].quantity;
                document.getElementById('price'+ response.data[i].productRef__productCode).innerHTML = parseFloat(response.data[i].pricePerItem).toFixed(2);
                document.getElementById('priceTotal'+ response.data[i].productRef__productCode).innerHTML = parseFloat(response.data[i].totalPrice).toFixed(2);                                
            }
        }
    })
    getTotalAmountInCart(transactionID);
}

function getTotalAmountInCart(transactionID){
    $.ajax({
        url: '/sales/salestotalamountincart',
        type: 'GET',
        dataType: 'json',
        data: {
            'transactionID': transactionID,
        },
        success: function (response){
            document.getElementById('amtToPay').innerHTML = parseFloat(response.totalAmount).toFixed(2);
            document.getElementById('totalAmount').innerHTML = parseFloat(response.totalAmount).toFixed(2);
        }
    })
}

document.addEventListener('DOMContentLoaded', (event) => {
    let transactionID = document.getElementById('salesTransactionID').value;
    displayAllCarts(transactionID);
    getTotalAmountInCart(transactionID);
});


function addToCart(opt, code){    
    let qty = document.getElementById('qty' + code);
    let transactionID = document.getElementById('salesTransactionID').value;
    displayAllCarts(transactionID);
    getTotalAmountInCart(transactionID);
    $.ajax({
        url: '/sales/salesaddtocat',
        type: 'POST',
        dataType: 'json',
        data: {
            'productCode': code,
            'quantity': qty.value,
            'opt': opt,
            'transactionID': transactionID,
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val(),
        },
        success: function (response){
            for(var i=0; i <= response.data.length; i++){
                if(response.data[i].quantity > 0)
                {
                    document.getElementById('cartPage'+ response.data[i].productRef__productCode).hidden=false;
                }
                else
                {
                    document.getElementById('cartPage'+ response.data[i].productRef__productCode).hidden=true;
                }
                document.getElementById('addQty'+ response.data[i].productRef__productCode).innerHTML = response.data[i].quantity;
                document.getElementById('price'+ response.data[i].productRef__productCode).innerHTML = parseFloat(response.data[i].pricePerItem).toFixed(2);
                document.getElementById('priceTotal'+ response.data[i].productRef__productCode).innerHTML = parseFloat(response.data[i].totalPrice).toFixed(2);
                       
            }
        },
        error: function (error){
            alert('error: operation failed!')
        }
    });
    getTotalAmountInCart(transactionID);
}





 
