"""
Data sorting utilities for organizing conversions and file data.
Provides various algorithms for sorting and organizing data.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Callable, Optional, Union

# Set up logging
logger = logging.getLogger(__name__)

class SortDirection(Enum):
    """Enum for sort direction"""
    ASCENDING = "asc"
    DESCENDING = "desc"

class SortAlgorithm(Enum):
    """Enum for sorting algorithms"""
    QUICK_SORT = "quick_sort"
    MERGE_SORT = "merge_sort"
    HEAP_SORT = "heap_sort"
    INSERTION_SORT = "insertion_sort"

class GroupingMethod(Enum):
    """Enum for grouping methods"""
    BY_DATE = "date"
    BY_FORMAT = "format"
    BY_SIZE = "size"
    BY_STATUS = "status"
    BY_USER = "user"
    BY_TIER = "tier"

class DataSorter:
    """Utility class for sorting and organizing data"""

    @staticmethod
    def sort_conversions(
        conversions: List[Dict[str, Any]],
        sort_by: str = "created_at",
        direction: SortDirection = SortDirection.DESCENDING,
        algorithm: SortAlgorithm = SortAlgorithm.QUICK_SORT
    ) -> List[Dict[str, Any]]:
        """
        Sort a list of conversions using the specified algorithm
        
        Args:
            conversions: List of conversion dictionaries to sort
            sort_by: Key to sort by
            direction: Sort direction (ascending or descending)
            algorithm: Sorting algorithm to use
            
        Returns:
            List of sorted conversions
        """
        if not conversions:
            return []
        
        # Clone the list to avoid modifying the original
        result = conversions.copy()
        
        # Select the sorting algorithm
        if algorithm == SortAlgorithm.QUICK_SORT:
            sorted_result = DataSorter._quick_sort(result, sort_by, direction)
        elif algorithm == SortAlgorithm.MERGE_SORT:
            sorted_result = DataSorter._merge_sort(result, sort_by, direction)
        elif algorithm == SortAlgorithm.HEAP_SORT:
            sorted_result = DataSorter._heap_sort(result, sort_by, direction)
        elif algorithm == SortAlgorithm.INSERTION_SORT:
            sorted_result = DataSorter._insertion_sort(result, sort_by, direction)
        else:
            logger.warning(f"Unknown sorting algorithm: {algorithm}, falling back to quick sort")
            sorted_result = DataSorter._quick_sort(result, sort_by, direction)
        
        return sorted_result
    
    @staticmethod
    def group_conversions(
        conversions: List[Dict[str, Any]],
        group_by: GroupingMethod
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group conversions by a specific attribute
        
        Args:
            conversions: List of conversions to group
            group_by: Grouping method to use
            
        Returns:
            Dictionary with groups as keys and lists of conversions as values
        """
        if not conversions:
            return {}
        
        grouped = {}
        
        if group_by == GroupingMethod.BY_DATE:
            # Group by date (day)
            for conversion in conversions:
                if "created_at" in conversion and conversion["created_at"]:
                    # Parse the date string to datetime
                    if isinstance(conversion["created_at"], str):
                        date = datetime.fromisoformat(conversion["created_at"].replace('Z', '+00:00'))
                    else:
                        date = conversion["created_at"]
                    
                    # Format as string
                    date_str = date.strftime("%Y-%m-%d")
                    
                    if date_str not in grouped:
                        grouped[date_str] = []
                    
                    grouped[date_str].append(conversion)
                else:
                    # Handle missing date
                    if "Unknown" not in grouped:
                        grouped["Unknown"] = []
                    grouped["Unknown"].append(conversion)
            
        elif group_by == GroupingMethod.BY_FORMAT:
            # Group by source and target format
            for conversion in conversions:
                format_key = f"{conversion.get('source_format', 'unknown')} to {conversion.get('target_format', 'unknown')}"
                
                if format_key not in grouped:
                    grouped[format_key] = []
                
                grouped[format_key].append(conversion)
                
        elif group_by == GroupingMethod.BY_SIZE:
            # Group by file size ranges
            size_ranges = {
                "0-1MB": (0, 1 * 1024 * 1024),
                "1-10MB": (1 * 1024 * 1024, 10 * 1024 * 1024),
                "10-50MB": (10 * 1024 * 1024, 50 * 1024 * 1024),
                "50-100MB": (50 * 1024 * 1024, 100 * 1024 * 1024),
                "100MB+": (100 * 1024 * 1024, float('inf'))
            }
            
            for conversion in conversions:
                # Get file size if available
                file_size = DataSorter._get_file_size(conversion)
                
                # Find the appropriate range
                size_range = "Unknown"
                for range_name, (min_size, max_size) in size_ranges.items():
                    if min_size <= file_size < max_size:
                        size_range = range_name
                        break
                
                if size_range not in grouped:
                    grouped[size_range] = []
                
                grouped[size_range].append(conversion)
                
        elif group_by == GroupingMethod.BY_STATUS:
            # Group by conversion status
            for conversion in conversions:
                status = conversion.get("status", "unknown")
                
                if status not in grouped:
                    grouped[status] = []
                
                grouped[status].append(conversion)
                
        elif group_by == GroupingMethod.BY_USER:
            # Group by user ID
            for conversion in conversions:
                user_id = conversion.get("user_id", "unknown")
                
                if user_id not in grouped:
                    grouped[user_id] = []
                
                grouped[user_id].append(conversion)
                
        elif group_by == GroupingMethod.BY_TIER:
            # This requires user information to be included in the conversion
            for conversion in conversions:
                tier = conversion.get("user_tier", "unknown")
                
                if tier not in grouped:
                    grouped[tier] = []
                
                grouped[tier].append(conversion)
        
        else:
            # Fallback: no grouping, just return everything in a single group
            grouped["all"] = conversions
        
        return grouped
    
    @staticmethod
    def filter_conversions(
        conversions: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter conversions based on criteria
        
        Args:
            conversions: List of conversions to filter
            filters: Dictionary of filter criteria
            
        Returns:
            Filtered list of conversions
        """
        if not conversions or not filters:
            return conversions
        
        result = conversions.copy()
        
        for key, value in filters.items():
            # Handle special case for date ranges
            if key == "date_range" and isinstance(value, dict):
                start = value.get("start")
                end = value.get("end")
                
                if start or end:
                    result = DataSorter._filter_by_date_range(result, start, end)
                continue
            
            # Handle special case for search string (looks in multiple fields)
            if key == "search":
                result = DataSorter._filter_by_search_term(result, value)
                continue
            
            # Handle special case for size ranges
            if key == "size_range" and isinstance(value, dict):
                min_size = value.get("min")
                max_size = value.get("max")
                
                if min_size is not None or max_size is not None:
                    result = DataSorter._filter_by_size_range(result, min_size, max_size)
                continue
            
            # Standard field filtering
            result = [item for item in result if DataSorter._matches_filter(item, key, value)]
        
        return result
    
    @staticmethod
    def paginate_results(
        items: List[Dict[str, Any]],
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Paginate results
        
        Args:
            items: List of items to paginate
            page: Page number (starting from 1)
            per_page: Items per page
            
        Returns:
            Dictionary with pagination info and items
        """
        if not items:
            return {
                "items": [],
                "page": page,
                "per_page": per_page,
                "total": 0,
                "total_pages": 0
            }
        
        # Validate page and per_page
        if page < 1:
            page = 1
        
        if per_page < 1:
            per_page = 10
        
        total = len(items)
        total_pages = (total + per_page - 1) // per_page  # Ceiling division
        
        # Adjust page if it's out of range
        if page > total_pages:
            page = total_pages
        
        # Calculate start and end indices
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total)
        
        # Get items for the current page
        paged_items = items[start_idx:end_idx]
        
        return {
            "items": paged_items,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages
        }
    
    @staticmethod
    def calculate_statistics(conversions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics about conversions
        
        Args:
            conversions: List of conversions
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_conversions": len(conversions),
            "successful_conversions": 0,
            "failed_conversions": 0,
            "formats": {},
            "average_size": 0,
            "conversions_by_date": {},
            "processing_time": {
                "average": 0,
                "max": 0,
                "min": float('inf')
            }
        }
        
        if not conversions:
            stats["processing_time"]["min"] = 0
            return stats
        
        total_size = 0
        total_processing_time = 0
        processing_times = []
        
        for conversion in conversions:
            # Count successful/failed conversions
            status = conversion.get("status", "").lower()
            if status == "completed":
                stats["successful_conversions"] += 1
            elif status == "failed":
                stats["failed_conversions"] += 1
            
            # Count formats
            source_format = conversion.get("source_format", "unknown")
            target_format = conversion.get("target_format", "unknown")
            format_key = f"{source_format} to {target_format}"
            
            if format_key not in stats["formats"]:
                stats["formats"][format_key] = 0
            stats["formats"][format_key] += 1
            
            # Calculate total size
            size = DataSorter._get_file_size(conversion)
            total_size += size
            
            # Count by date
            created_at = conversion.get("created_at")
            if created_at:
                if isinstance(created_at, str):
                    date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    date = created_at
                
                date_str = date.strftime("%Y-%m-%d")
                
                if date_str not in stats["conversions_by_date"]:
                    stats["conversions_by_date"][date_str] = 0
                stats["conversions_by_date"][date_str] += 1
            
            # Calculate processing time
            if conversion.get("completed_at") and conversion.get("created_at"):
                try:
                    if isinstance(conversion["completed_at"], str):
                        completed_at = datetime.fromisoformat(conversion["completed_at"].replace('Z', '+00:00'))
                    else:
                        completed_at = conversion["completed_at"]
                    
                    if isinstance(conversion["created_at"], str):
                        created_at = datetime.fromisoformat(conversion["created_at"].replace('Z', '+00:00'))
                    else:
                        created_at = conversion["created_at"]
                    
                    # Calculate time difference in seconds
                    time_diff = (completed_at - created_at).total_seconds()
                    processing_times.append(time_diff)
                    total_processing_time += time_diff
                    
                    # Update min/max
                    stats["processing_time"]["max"] = max(stats["processing_time"]["max"], time_diff)
                    stats["processing_time"]["min"] = min(stats["processing_time"]["min"], time_diff)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error calculating processing time: {e}")
        
        # Calculate averages
        if stats["total_conversions"] > 0:
            stats["average_size"] = total_size / stats["total_conversions"]
        
        if processing_times:
            stats["processing_time"]["average"] = total_processing_time / len(processing_times)
        else:
            stats["processing_time"]["min"] = 0
        
        return stats
    
    # Private helper methods
    
    @staticmethod
    def _quick_sort(items: List[Dict[str, Any]], sort_by: str, direction: SortDirection) -> List[Dict[str, Any]]:
        """Quick sort implementation"""
        if len(items) <= 1:
            return items
        
        # Implementation of quicksort
        def _partition(arr, low, high):
            # Select pivot (middle element)
            pivot_idx = (low + high) // 2
            pivot = DataSorter._get_sort_value(arr[pivot_idx], sort_by)
            
            # Move pivot to the end
            arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]
            
            # Partition around pivot
            i = low - 1
            for j in range(low, high):
                curr_val = DataSorter._get_sort_value(arr[j], sort_by)
                
                # Compare based on direction
                if (direction == SortDirection.ASCENDING and curr_val <= pivot) or \
                   (direction == SortDirection.DESCENDING and curr_val >= pivot):
                    i += 1
                    arr[i], arr[j] = arr[j], arr[i]
            
            # Move pivot to its final position
            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            return i + 1
        
        def _quick_sort_recursive(arr, low, high):
            if low < high:
                # Partition and get pivot index
                pivot_idx = _partition(arr, low, high)
                
                # Recursively sort the subarrays
                _quick_sort_recursive(arr, low, pivot_idx - 1)
                _quick_sort_recursive(arr, pivot_idx + 1, high)
        
        # Make a copy to avoid modifying original
        result = items.copy()
        
        # Sort the copy
        _quick_sort_recursive(result, 0, len(result) - 1)
        
        return result
    
    @staticmethod
    def _merge_sort(items: List[Dict[str, Any]], sort_by: str, direction: SortDirection) -> List[Dict[str, Any]]:
        """Merge sort implementation"""
        if len(items) <= 1:
            return items
        
        # Make a copy to avoid modifying original
        result = items.copy()
        
        def _merge(arr, temp, left, mid, right):
            # Copy data to temp arrays
            for i in range(left, right + 1):
                temp[i] = arr[i]
            
            i = left  # Initial index of first subarray
            j = mid + 1  # Initial index of second subarray
            k = left  # Initial index of merged subarray
            
            # Merge the temp arrays back
            while i <= mid and j <= right:
                val_i = DataSorter._get_sort_value(temp[i], sort_by)
                val_j = DataSorter._get_sort_value(temp[j], sort_by)
                
                # Compare based on direction
                if (direction == SortDirection.ASCENDING and val_i <= val_j) or \
                   (direction == SortDirection.DESCENDING and val_i >= val_j):
                    arr[k] = temp[i]
                    i += 1
                else:
                    arr[k] = temp[j]
                    j += 1
                k += 1
            
            # Copy the remaining elements
            while i <= mid:
                arr[k] = temp[i]
                i += 1
                k += 1
            
            while j <= right:
                arr[k] = temp[j]
                j += 1
                k += 1
        
        def _merge_sort_recursive(arr, temp, left, right):
            if left < right:
                mid = (left + right) // 2
                
                # Sort first and second halves
                _merge_sort_recursive(arr, temp, left, mid)
                _merge_sort_recursive(arr, temp, mid + 1, right)
                
                # Merge the sorted halves
                _merge(arr, temp, left, mid, right)
        
        # Create a temporary array
        temp = [None] * len(result)
        
        # Sort
        _merge_sort_recursive(result, temp, 0, len(result) - 1)
        
        return result
    
    @staticmethod
    def _heap_sort(items: List[Dict[str, Any]], sort_by: str, direction: SortDirection) -> List[Dict[str, Any]]:
        """Heap sort implementation"""
        if len(items) <= 1:
            return items
        
        # Make a copy to avoid modifying original
        result = items.copy()
        n = len(result)
        
        # Build a max/min heap based on direction
        for i in range(n // 2 - 1, -1, -1):
            DataSorter._heapify(result, n, i, sort_by, direction)
        
        # Extract elements from heap one by one
        for i in range(n - 1, 0, -1):
            result[0], result[i] = result[i], result[0]  # Swap
            
            # Heapify the reduced heap
            DataSorter._heapify(result, i, 0, sort_by, direction)
        
        return result
    
    @staticmethod
    def _heapify(arr, n, i, sort_by, direction):
        """Heapify a subtree rooted at index i"""
        largest = i  # Initialize largest as root
        left = 2 * i + 1
        right = 2 * i + 2
        
        # Compare left child with root
        if left < n:
            root_val = DataSorter._get_sort_value(arr[largest], sort_by)
            left_val = DataSorter._get_sort_value(arr[left], sort_by)
            
            if (direction == SortDirection.ASCENDING and left_val > root_val) or \
               (direction == SortDirection.DESCENDING and left_val < root_val):
                largest = left
        
        # Compare right child with largest so far
        if right < n:
            largest_val = DataSorter._get_sort_value(arr[largest], sort_by)
            right_val = DataSorter._get_sort_value(arr[right], sort_by)
            
            if (direction == SortDirection.ASCENDING and right_val > largest_val) or \
               (direction == SortDirection.DESCENDING and right_val < largest_val):
                largest = right
        
        # Change root if needed
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]  # Swap
            
            # Recursively heapify the affected sub-tree
            DataSorter._heapify(arr, n, largest, sort_by, direction)
    
    @staticmethod
    def _insertion_sort(items: List[Dict[str, Any]], sort_by: str, direction: SortDirection) -> List[Dict[str, Any]]:
        """Insertion sort implementation"""
        if len(items) <= 1:
            return items
        
        # Make a copy to avoid modifying original
        result = items.copy()
        
        # Traverse through 1 to len(result)
        for i in range(1, len(result)):
            key = result[i]
            key_val = DataSorter._get_sort_value(key, sort_by)
            
            # Move elements greater than key to one position ahead
            j = i - 1
            while j >= 0:
                curr_val = DataSorter._get_sort_value(result[j], sort_by)
                
                # Compare based on direction
                if (direction == SortDirection.ASCENDING and curr_val > key_val) or \
                   (direction == SortDirection.DESCENDING and curr_val < key_val):
                    result[j + 1] = result[j]
                    j -= 1
                else:
                    break
            
            result[j + 1] = key
        
        return result
    
    @staticmethod
    def _get_sort_value(item: Dict[str, Any], key: str) -> Any:
        """Extract the value to sort by from the item"""
        # Handle nested keys (e.g., 'user.name')
        if '.' in key:
            parts = key.split('.')
            value = item
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            
            return value
        
        # Handle regular keys
        return item.get(key)
    
    @staticmethod
    def _filter_by_date_range(
        items: List[Dict[str, Any]],
        start_date: Optional[Union[str, datetime]],
        end_date: Optional[Union[str, datetime]]
    ) -> List[Dict[str, Any]]:
        """Filter items by date range"""
        if not start_date and not end_date:
            return items
        
        result = []
        
        # Convert string dates to datetime objects
        if start_date and isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid start date format: {start_date}")
                start_date = None
        
        if end_date and isinstance(end_date, str):
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid end date format: {end_date}")
                end_date = None
        
        # Filter items
        for item in items:
            created_at = item.get("created_at")
            
            if not created_at:
                continue
            
            # Convert string date to datetime
            if isinstance(created_at, str):
                try:
                    item_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Invalid date format in item: {created_at}")
                    continue
            else:
                item_date = created_at
            
            # Check if the item is within the date range
            if start_date and item_date < start_date:
                continue
            
            if end_date and item_date > end_date:
                continue
            
            result.append(item)
        
        return result
    
    @staticmethod
    def _filter_by_search_term(items: List[Dict[str, Any]], search_term: str) -> List[Dict[str, Any]]:
        """Filter items by search term (searches multiple fields)"""
        if not search_term:
            return items
        
        search_term = search_term.lower()
        result = []
        
        # Fields to search in
        search_fields = ["source_filename", "target_filename", "source_format", "target_format", "status"]
        
        for item in items:
            # Check if any field contains the search term
            for field in search_fields:
                value = item.get(field)
                
                if value and isinstance(value, str) and search_term in value.lower():
                    result.append(item)
                    break
        
        return result
    
    @staticmethod
    def _filter_by_size_range(
        items: List[Dict[str, Any]],
        min_size: Optional[int],
        max_size: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Filter items by file size range"""
        if min_size is None and max_size is None:
            return items
        
        result = []
        
        for item in items:
            size = DataSorter._get_file_size(item)
            
            # Check if the size is within the range
            if min_size is not None and size < min_size:
                continue
            
            if max_size is not None and size > max_size:
                continue
            
            result.append(item)
        
        return result
    
    @staticmethod
    def _matches_filter(item: Dict[str, Any], key: str, value: Any) -> bool:
        """Check if an item matches a specific filter"""
        # Handle nested keys (e.g., 'user.name')
        if '.' in key:
            parts = key.split('.')
            current = item
            
            for part in parts[:-1]:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return False
            
            # Check the final key
            final_key = parts[-1]
            if isinstance(current, dict) and final_key in current:
                return current[final_key] == value
            
            return False
        
        # Handle regular keys
        item_value = item.get(key)
        
        # Handle lists (check if value is in the list)
        if isinstance(item_value, list):
            return value in item_value
        
        # Handle regular equality check
        return item_value == value
    
    @staticmethod
    def _get_file_size(item: Dict[str, Any]) -> int:
        """Extract file size from an item"""
        # Try to get file size from different possible fields
        for field in ["file_size", "source_file_size", "size"]:
            if field in item and item[field] is not None:
                return int(item[field])
        
        return 0 