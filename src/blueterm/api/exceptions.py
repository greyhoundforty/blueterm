"""Custom exceptions for IBM Cloud VPC API operations"""


class BluetermException(Exception):
    """Base exception for all blueterm errors"""
    pass


class AuthenticationError(BluetermException):
    """Raised when authentication with IBM Cloud fails"""
    pass


class RegionError(BluetermException):
    """Raised when region operations fail"""
    pass


class InstanceError(BluetermException):
    """Raised when instance operations fail"""
    pass


class ConfigurationError(BluetermException):
    """Raised when configuration is invalid or missing"""
    pass
