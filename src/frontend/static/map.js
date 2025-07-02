let map;
let destinations = [];
let selectedLocations = new Set();
let markers = [];

// Initialize the map and load data
async function initMap() {
  try {
    const response = await fetch('/destinations');
    destinations = await response.json();

    map = new google.maps.Map(document.getElementById("map"), {
      zoom: 10,
      center: destinations.length ? { lat: destinations[0].lat, lng: destinations[0].lng } : { lat: 0, lng: 0 },
    });

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
        toggleLocationSelection(index);
      });

      markers.push(marker);
    });

    // Load user trips and locations
    await loadUserTrips();
    await loadLocationsList();
    
    // Setup mobile sidebar toggle
    setupMobileSidebar();
    
  } catch (error) {
    console.error('Error initializing map:', error);
    showError('Failed to load map data');
  }
}

// Load user trips for the dropdown
async function loadUserTrips() {
  try {
    const response = await fetch('/api/user/trips');
    const data = await response.json();
    
    const tripSelect = document.getElementById('tripSelect');
    tripSelect.innerHTML = '<option value="">Choose a trip...</option>';
    
    if (data.success && data.trips.length > 0) {
      data.trips.forEach(trip => {
        const option = document.createElement('option');
        option.value = trip.id;
        option.textContent = trip.name;
        tripSelect.appendChild(option);
      });
    }
  } catch (error) {
    console.error('Error loading trips:', error);
  }
}

// Load locations list in sidebar
async function loadLocationsList() {
  const locationsList = document.getElementById('locationsList');
  
  if (destinations.length === 0) {
    locationsList.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">No locations available</div>';
    return;
  }
  
  locationsList.innerHTML = '';
  
  destinations.forEach((dest, index) => {
    const locationItem = document.createElement('div');
    locationItem.className = 'location-item';
    locationItem.dataset.index = index;
    
    locationItem.innerHTML = `
      <div class="location-name">${dest.name}</div>
      <div class="location-coords">${dest.lat.toFixed(4)}, ${dest.lng.toFixed(4)}</div>
    `;
    
    locationItem.addEventListener('click', () => {
      toggleLocationSelection(index);
    });
    
    locationsList.appendChild(locationItem);
  });
}

// Toggle location selection
function toggleLocationSelection(index) {
  const locationItem = document.querySelector(`[data-index="${index}"]`);
  
  if (selectedLocations.has(index)) {
    selectedLocations.delete(index);
    locationItem.classList.remove('selected');
    markers[index].setLabel((index + 1).toString());
  } else {
    selectedLocations.add(index);
    locationItem.classList.add('selected');
    markers[index].setLabel('✓');
  }
  
  updateSaveButton();
}

// Update save button state
function updateSaveButton() {
  const saveBtn = document.getElementById('saveLocationsBtn');
  const tripSelect = document.getElementById('tripSelect');
  
  saveBtn.disabled = selectedLocations.size === 0 || !tripSelect.value;
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

// Create new trip
async function createTrip() {
  const name = document.getElementById('tripName').value.trim();
  const description = document.getElementById('tripDescription').value.trim();
  
  if (!name) {
    showError('Trip name is required');
    return;
  }
  
  try {
    const response = await fetch('/api/trips', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, description })
    });
    
    const data = await response.json();
    
    if (data.success) {
      showSuccess('Trip created successfully!');
      document.getElementById('newTripForm').classList.remove('show');
      document.getElementById('tripName').value = '';
      document.getElementById('tripDescription').value = '';
      await loadUserTrips();
      
      // Select the newly created trip
      const tripSelect = document.getElementById('tripSelect');
      tripSelect.value = data.trip.id;
      updateSaveButton();
    } else {
      showError(data.error || 'Failed to create trip');
    }
  } catch (error) {
    console.error('Error creating trip:', error);
    showError('Failed to create trip');
  }
}

// Save selected locations to trip
async function saveLocationsToTrip() {
  const tripId = document.getElementById('tripSelect').value;
  
  if (!tripId) {
    showError('Please select a trip');
    return;
  }
  
  if (selectedLocations.size === 0) {
    showError('Please select at least one location');
    return;
  }
  
  const locationsToSave = Array.from(selectedLocations).map(index => destinations[index]);
  
  try {
    const response = await fetch(`/api/trips/${tripId}/locations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ locations: locationsToSave })
    });
    
    const data = await response.json();
    
    if (data.success) {
      showSuccess(data.message);
      // Clear selections
      selectedLocations.clear();
      destinations.forEach((_, index) => {
        const locationItem = document.querySelector(`[data-index="${index}"]`);
        if (locationItem) {
          locationItem.classList.remove('selected');
        }
        markers[index].setLabel((index + 1).toString());
      });
      updateSaveButton();
    } else {
      showError(data.error || 'Failed to save locations');
    }
  } catch (error) {
    console.error('Error saving locations:', error);
    showError('Failed to save locations');
  }
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

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
  // New trip button
  document.getElementById('newTripBtn').addEventListener('click', () => {
    document.getElementById('newTripForm').classList.toggle('show');
  });
  
  // Create trip button
  document.getElementById('createTripBtn').addEventListener('click', createTrip);
  
  // Save locations button
  document.getElementById('saveLocationsBtn').addEventListener('click', saveLocationsToTrip);
  
  // Trip select change
  document.getElementById('tripSelect').addEventListener('change', updateSaveButton);
});

// Initialize map when Google Maps API is loaded
window.onload = initMap;