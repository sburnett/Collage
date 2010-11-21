function cancelFromThumb(cancelEl) {
    var spanEl = cancelEl.parentNode;

    makeRequest("/thumbnail_cancel?filename=" + escape(spanEl.getAttribute("filename")));

    var parEl = spanEl.parentNode;
    parEl.removeChild(spanEl);
    updateVectorIds();
}

function makeRequest(url) {
    var http_request = false;
    if (window.XMLHttpRequest) { // Mozilla, Safari,...
        http_request = new XMLHttpRequest();
        if (http_request.overrideMimeType) {
            http_request.overrideMimeType('text/xml');
        }
    } else if (window.ActiveXObject) { // IE
        try {
            http_request = new ActiveXObject("Msxml2.XMLHTTP");
        } catch (e) {
            try {
                http_request = new ActiveXObject("Microsoft.XMLHTTP");
            } catch (e) {}
        }
    }
    if (!http_request) {
        return false;
    }

//    http_request.onreadystatechange = alertContents;
    http_request.open('GET', url, true);
    http_request.send(null);
}

function updateVectorIds() {
    var spans = document.getElementsByName("thumbnail");
    var filenames = new Array();
    for(var i = 0; i < spans.length; i++) {
        filenames.push(spans[i].getAttribute("filename"));
    }
    document.getElementById("vector_ids").value = filenames.join(";");
}

function addImage(src, filename, fade) {
	var newImg = document.createElement("img");
	newImg.style.margin = "5px";

    var thumbCancel = document.createElement("a");
    thumbCancel.className = "thumbCancel";
    thumbCancel.href = "#";
    thumbCancel.setAttribute("onclick", "cancelFromThumb(this);");
    thumbCancel.appendChild(document.createTextNode(" "));

    var newSpan = document.createElement("span");
    newSpan.style.position = "relative";
    newSpan.setAttribute("name", "thumbnail");
    newSpan.setAttribute("filename", filename);
    newSpan.appendChild(newImg);
    newSpan.appendChild(thumbCancel);
	document.getElementById("thumbnails").appendChild(newSpan);

    if(fade) {
        if (newImg.filters) {
            try {
                newImg.filters.item("DXImageTransform.Microsoft.Alpha").opacity = 0;
            } catch (e) {
                // If it is not set initially, the browser will throw an error.  This will set it if it is not set yet.
                newImg.style.filter = 'progid:DXImageTransform.Microsoft.Alpha(opacity=' + 0 + ')';
            }
        } else {
            newImg.style.opacity = 0;
        }

        newImg.onload = function () {
            fadeIn(newImg, 0);
        };
    }
	newImg.src = src;
}

function fadeIn(element, opacity) {
	var reduceOpacityBy = 5;
	var rate = 30;	// 15 fps


	if (opacity < 100) {
		opacity += reduceOpacityBy;
		if (opacity > 100) {
			opacity = 100;
		}

		if (element.filters) {
			try {
				element.filters.item("DXImageTransform.Microsoft.Alpha").opacity = opacity;
			} catch (e) {
				// If it is not set initially, the browser will throw an error.  This will set it if it is not set yet.
				element.style.filter = 'progid:DXImageTransform.Microsoft.Alpha(opacity=' + opacity + ')';
			}
		} else {
			element.style.opacity = opacity / 100;
		}
	}

	if (opacity < 100) {
		setTimeout(function () {
			fadeIn(element, opacity);
		}, rate);
	}
}
