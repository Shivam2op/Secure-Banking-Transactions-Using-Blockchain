if (document.addEventListener)
    {
        document.addEventListener('contextmenu', function(e) {
            alert("Due to security reasons, Right Click is not allowed.");
            e.preventDefault();
        }, false);
    }
else
    {
        document.attachEvent('oncontextmenu', function() {
            alert("Due to security reasons, Right Click is not allowed.");
            window.event.returnValue = false;
        });
    }