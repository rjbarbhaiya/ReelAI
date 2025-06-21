async function initMap() {
  const response = await fetch('/destinations');
  const destinations = await response.json();

  map = new google.maps.Map(document.getElementById("map"), {
    zoom: 10,
    center: destinations.length ? { lat: destinations[0].lat, lng: destinations[0].lng } : { lat: 0, lng: 0 },
  });

  destinations.forEach(dest => {
    new google.maps.Marker({
      position: { lat: dest.lat, lng: dest.lng },
      map,
      title: dest.name,
    });
  });
}

window.onload = initMap;