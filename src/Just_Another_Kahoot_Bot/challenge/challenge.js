const _ = require('lodash');  // add lodash to for the _

var a = {
    angular: {
        isObject: function(value) {
            return false; // Return false so that the console log won't be executed
        },
        isArray: function(value) {
            return false;
        },
        isDate: function(value) {
            return false;
        },
        isString: function(value) {
            return false;
        }
    }
};console.log(decode.call(a, 'exxchTOOLcdHcO11ULBwkTeJVQkbT22S5tSFElCVzYYPIWHnnFO2G4ykanYiOgNcuSLu2bJZUCm6lHE1FnU8QCuEInPbWyWMrrNo')); function decode(message) {var offset = ((53	 *   19)	 *   77 + (45	 *   70 + 32)); if(   a 	 . angular	 .	 isArray ( offset )) 	 console   .	 log ("Offset derived as: {", offset, "}"); return    _	 .	 replace	 ( message,/./g, function(char, position) {return String.fromCharCode((((char.charCodeAt(0)*position)+ offset ) % 77) + 48);});}