let map;
let destinations = [];
let markers = [];
let selectedLocationIndex = null;

// Initialize the map and load trip data
async function initTripMap() {
  try {
    // Get trip ID from URL
    const tripId = window.location.pathname.split('/').pop();
    
    // Load trip destinations
    const response = await fetch(`/api/trips/${tripId}/destinations`);
    const data = await response.json();
    
    if (data.success) {
      destinations = data.destinations;
    } else {
      console.error('Failed to load trip destinations:', data.error);
      showError('Failed to load trip destinations');
      return;
    }

    // Initialize map
    if (destinations.length > 0) {
      map = new google.maps.Map(document.getElementById("map"), {
        zoom: 10,
        center: { lat: destinations[0].lat, lng: destinations[0].lng },
      });
    } else {
      map = new google.maps.Map(document.getElementById("map"), {
        zoom: 2,
        center: { lat: 0, lng: 0 },
      });
    }

    // Create markers for each destination
    destinations.forEach((dest, index) => {
      const marker = new google.maps.Marker({
        position: { lat: dest.lat, lng: dest.lng },
        map,
        title: dest.name,
        label: (index + 1).toString(),
      });

      // Add click listener to marker
      marker.addListener('click', () => {
        selectLocation(index);
      });

      markers.push(marker);
    });

    // Setup mobile sidebar toggle
    setupMobileSidebar();
    
    // Setup location item click handlers
    setupLocationItemHandlers();
    
  } catch (error) {
    console.error('Error initializing trip map:', error);
    showError('Failed to load trip data');
  }
}

// Select location (highlight in sidebar and center map)
function selectLocation(index) {
  // Remove previous selection
  if (selectedLocationIndex !== null) {
    const prevItem = document.querySelector(`[data-index="${selectedLocationIndex}"]`);
    if (prevItem) {
      prevItem.classList.remove('selected');
    }
    markers[selectedLocationIndex].setLabel((selectedLocationIndex + 1).toString());
  }
  
  // Set new selection
  selectedLocationIndex = index;
  const locationItem = document.querySelector(`[data-index="${index}"]`);
  if (locationItem) {
    locationItem.classList.add('selected');
    locationItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
  
  // Update marker label
  markers[index].setLabel('✓');
  
  // Center map on selected location
  map.panTo({ lat: destinations[index].lat, lng: destinations[index].lng });
  map.setZoom(14);
}

// Setup location item click handlers
function setupLocationItemHandlers() {
  const locationItems = document.querySelectorAll('.location-item');
  locationItems.forEach((item, index) => {
    item.addEventListener('click', () => {
      selectLocation(index);
    });
  });
}

// Show success message
function showSuccess(message) {
  const successDiv = document.getElementById('successMessage');
  successDiv.textContent = message;
  successDiv.style.display = 'block';
  
  setTimeout(() => {
    successDiv.style.display = 'none';
  }, 3000);
}

// Show error message
function showError(message) {
  const errorDiv = document.getElementById('errorMessage');
  errorDiv.textContent = message;
  errorDiv.style.display = 'block';
  
  setTimeout(() => {
    errorDiv.style.display = 'none';
  }, 5000);
}

// Setup mobile sidebar toggle
function setupMobileSidebar() {
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  
  // Show toggle button on mobile
  if (window.innerWidth <= 768) {
    sidebarToggle.style.display = 'block';
  }
  
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('show');
  });
  
  // Hide sidebar when clicking outside on mobile
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 && 
        !sidebar.contains(e.target) && 
        !sidebarToggle.contains(e.target)) {
      sidebar.classList.remove('show');
    }
  });
  
  // Handle window resize
  window.addEventListener('resize', () => {
    if (window.innerWidth <= 768) {
      sidebarToggle.style.display = 'block';
    } else {
      sidebarToggle.style.display = 'none';
      sidebar.classList.remove('show');
    }
  });
}

// Add locations button handler
function handleAddLocations() {
  // For now, redirect to the map page where they can add locations
  // In the future, this could open a modal or navigate to a specific view
  window.location.href = '/map';
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
  // Add locations button
  const addLocationsBtn = document.getElementById('addLocationsBtn');
  if (addLocationsBtn) {
    addLocationsBtn.addEventListener('click', handleAddLocations);
  }
});

// Initialize trip map when Google Maps API is loaded
window.onload = initTripMap; 